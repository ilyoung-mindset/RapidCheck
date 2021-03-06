from . pascal_voc_clean_xml import pascal_voc_clean_xml
from yolo.process import preprocess
from numpy.random import permutation as perm
from copy import deepcopy
import pickle
import numpy as np
import os
import yolo.config as cfg

def _make_datacetner_folder(new_folder_path):
	os.mkdir(new_folder_path)
	os.mkdir(os.path.join(new_folder_path, "annotations"))
	os.mkdir(os.path.join(new_folder_path, "images"))
	return new_folder_path

def _video_walk(cached_hash_ids, datacenter_root, dataset_enduser_root):
	from shutil import copyfile
	
	new_hash_ids = []
	if not os.path.exists(dataset_enduser_root):
		# 없으면 enduser_root 를 만든다
		_make_datacetner_folder(dataset_enduser_root)

	if not os.path.exists(os.path.join(dataset_enduser_root, 'annotations')):
		os.mkdir(os.path.join(dataset_enduser_root, 'annotations'))
	if not os.path.exists(os.path.join(dataset_enduser_root, 'images')):
		os.mkdir(os.path.join(dataset_enduser_root, 'images'))

	for folder, subfolders, files in os.walk(datacenter_root):
		folder_name = folder.split(os.sep)[-1]
		if 'video_' in folder_name:
			hash_id = folder_name.split('_')[1]
			if hash_id in cached_hash_ids:
				# get video hash_id for duplicate check
				continue
			new_hash_ids.append(hash_id)
			each_anno_folder = os.path.join(folder, 'annotations')
			each_image_folder = os.path.join(folder, 'images')

			anno_files = [f for f in os.listdir(each_anno_folder) if f.split('.')[-1] == 'xml' or f.split('.')[-1] == 'png']
			for anno_file in anno_files:
				copyfile(os.path.join(each_anno_folder, anno_file), os.path.join(dataset_enduser_root, 'annotations', anno_file))
				copyfile(os.path.join(each_image_folder, anno_file.split('.')[0]+'.png'), os.path.join(dataset_enduser_root, 'images', anno_file.split('.')[0]+'.png'))

	
	return new_hash_ids

def split_datacenter(src_folder_path, train_rates=0.8):
	"""
		datacenter/
			annotations/
			images/
		로 나눠져있는 데이터에 대해서 train_rates 만큼 trainval 과 test set 으로 나눠주는 기능을 담당할 것
		src_folder_path 는 datacenter 가 올것이고
		src_folder_path + '_trainval',
		src_folder_path + '_test' 아래에 annotations/ 와 images/ 가 생성될 예정이다.
		return trainval_indexs, test_indexs
	"""
	from shutil import copyfile, rmtree
	
	src_anno_path = os.path.join(src_folder_path, 'annotations')
	src_images_path = os.path.join(src_folder_path, 'images')
	anno_files, trainval_indexs, test_indexs = _split(src_anno_path, train_rates)
	
	if not os.path.exists(os.path.join(src_folder_path, 'trainval')):
		trainval_folder_path = _make_datacetner_folder(os.path.join(src_folder_path, 'trainval'))
	else:
		rmtree(os.path.join(src_folder_path, 'trainval'))
		trainval_folder_path = _make_datacetner_folder(os.path.join(src_folder_path, 'trainval'))
	
	if not os.path.exists(os.path.join(src_folder_path, 'test')):
		test_folder_path = _make_datacetner_folder(os.path.join(src_folder_path, 'test'))
	else:
		rmtree(os.path.join(src_folder_path, 'test'))
		test_folder_path = _make_datacetner_folder(os.path.join(src_folder_path, 'test'))
	
	# Make trainval datacenter folder
	for i in trainval_indexs:
		# print("trainval : ", i)
		copyfile(os.path.join(src_anno_path, anno_files[i]), os.path.join(trainval_folder_path, 'annotations', anno_files[i]))
		copyfile(os.path.join(src_images_path, anno_files[i].split('.')[0]+'.png'), os.path.join(trainval_folder_path, 'images', anno_files[i].split('.')[0]+'.png'))
	
	# Make test datacenter folder
	for i in test_indexs:
		# print("test : ", i)
		copyfile(os.path.join(src_anno_path, anno_files[i]), os.path.join(test_folder_path, 'annotations', anno_files[i]))
		copyfile(os.path.join(src_images_path, anno_files[i].split('.')[0]+'.png'), os.path.join(test_folder_path, 'images', anno_files[i].split('.')[0]+'.png'))

def _split(folder_path, train_rates=0.8):
	from numpy.random import permutation as perm
	import numpy as np
	files = [f for f in os.listdir(folder_path) if f.split('.')[-1] == 'xml' or f.split('.')[-1] == 'png']
	files_size = len(files)
	shuffle_idx = perm(np.arange(files_size))
	trainval_size = int(files_size*train_rates)
	return files, shuffle_idx[:trainval_size], shuffle_idx[trainval_size:]


def collect_enduser_trainset():
	import json
	if os.path.exists(os.path.join('yolo', 'parse-history.txt')):
		os.remove(os.path.join('yolo', 'parse-history.txt'))
		os.remove(os.path.join('yolo', 'enduser_custom_train.parsed'))
	
	infomation_file = os.path.join(cfg.dataset_enduser_root, 'infomation.json')
	with open(infomation_file, 'r') as f:
		infomation_json = json.load(f)
		if infomation_json['video_ids'] is None:
			infomation_json['video_ids'] = []
		new_hash_ids = _video_walk(infomation_json['video_ids'], cfg.datacenter_root, cfg.dataset_enduser_root)
		infomation_json['video_ids'] += new_hash_ids
	
	with open(infomation_file, 'w') as f:	
		json.dump(infomation_json, f)


	split_datacenter(cfg.dataset_enduser_root, train_rates=0.8)


def parse(exclusive = False):
	"""
	Decide whether to parse the annotation or not, 
	If the parsed file is not already there, parse.
	"""
	ext = '.parsed'
	history = os.path.join('yolo', 'parse-history.txt');
	if not os.path.isfile(history):
		file = open(history, 'w')
		file.close()
	with open(history, 'r') as f:
		lines = f.readlines()
	for line in lines:
		line = line.strip().split(' ')
		labels = line[1:]
		if labels == cfg.classes_name:
			if os.path.isfile(line[0]):
				with open(line[0], 'rb') as f:
					return pickle.load(f, encoding = 'latin1')[0]

	# actual parsing
	ann = cfg.ann_location
	if not os.path.isdir(ann):
		msg = 'Annotation directory not found {} .'
		exit('Error: {}'.format(msg.format(ann)))
	print('\n{} parsing {}'.format(cfg.model_name, ann))
	dumps = pascal_voc_clean_xml(ann, cfg.classes_name, exclusive)

	save_to = os.path.join('yolo', cfg.model_name)
	while True:
		if not os.path.isfile(save_to + ext): break
		save_to = save_to + '_'
	save_to += ext

	with open(save_to, 'wb') as f:
		pickle.dump([dumps], f, protocol = -1)
	with open(history, 'a') as f:
		f.write('{} '.format(save_to))
		f.write(' '.join(cfg.classes_name))
		f.write('\n')
	print('Result saved to {}'.format(save_to))
	return dumps


def flipChunk(chunk):
	# chunk[0] = chunk[0](before .) + 'reverse' + '.jpg'
	width = chunk[1][0]
	height = chunk[1][1]
	objs = chunk[1][2]
	for obj in objs:
		xmin = obj[1]
		xmax = obj[3]
		# obj[1] = width -1 - xmax
		obj[1] = width - xmax
		obj[3] = width - xmin

def chunkToXml(chunk):
	pass

def _batch(chunk, is_test=False):
	"""
	Takes a chunk of parsed annotations
	returns value for placeholders of net's 
	input & loss layer correspond to this chunk
	chunk : ['006098.jpg', [375, 500, [['boat', 92, 74, 292, 178], ['bird', 239, 88, 276, 133], ['bird', 93, 100, 142, 140]]]]
	"""
	S, B = cfg.cell_size, cfg.boxes_per_cell
	C, labels = cfg.num_classes, cfg.classes_name

	# preprocess
	jpg = chunk[0]; w, h, allobj_ = chunk[1]
	allobj = deepcopy(allobj_)
	if not is_test:
		path = os.path.join(cfg.imageset_location, jpg)
	else:
		path = os.path.join(cfg.test_imageset_location, jpg)
	img = preprocess(path, allobj)

	# Calculate regression target
	cellx = 1. * w / S
	celly = 1. * h / S
	for obj in allobj:
		centerx = .5*(obj[1]+obj[3]) #xmin, xmax
		centery = .5*(obj[2]+obj[4]) #ymin, ymax
		cx = centerx / cellx
		cy = centery / celly
		if cx >= S or cy >= S: return None, None
		obj[3] = float(obj[3]-obj[1]) / w
		obj[4] = float(obj[4]-obj[2]) / h
		obj[3] = np.sqrt(obj[3])
		obj[4] = np.sqrt(obj[4])
		obj[1] = cx - np.floor(cx) # centerx
		obj[2] = cy - np.floor(cy) # centery
		obj += [int(np.floor(cy) * S + np.floor(cx))]

	# show(im, allobj, S, w, h, cellx, celly) # unit test

	# Calculate placeholders' values
	probs = np.zeros([S*S,C])
	confs = np.zeros([S*S,B])
	coord = np.zeros([S*S,B,4])
	proid = np.zeros([S*S,C])
	prear = np.zeros([S*S,4])
	for obj in allobj:
		# print(type(obj), obj) # <class 'list'> ['horse', 0.024000000000000021, 0.48952095808383245, 0.92303846073714613, 0.85995404416970578, 24]
		probs[obj[5], :] = [0.] * C
		probs[obj[5], labels.index(obj[0])] = 1.
		proid[obj[5], :] = [1] * C
		coord[obj[5], :, :] = [obj[1:5]] * B
		prear[obj[5],0] = obj[1] - obj[3]**2 * .5 * S # xleft
		prear[obj[5],1] = obj[2] - obj[4]**2 * .5 * S # yup
		prear[obj[5],2] = obj[1] + obj[3]**2 * .5 * S # xright
		prear[obj[5],3] = obj[2] + obj[4]**2 * .5 * S # ybot
		confs[obj[5], :] = [1.] * B

	# Finalise the placeholders' values
	upleft   = np.expand_dims(prear[:,0:2], 1)
	botright = np.expand_dims(prear[:,2:4], 1)
	wh = botright - upleft; 
	area = wh[:,:,0] * wh[:,:,1]
	upleft   = np.concatenate([upleft] * B, 1)
	botright = np.concatenate([botright] * B, 1)
	areas = np.concatenate([area] * B, 1)

	# value for placeholder at input layer
	inp_feed_val = img
	# value for placeholder at loss layer 
	loss_feed_val = {
		'probs': probs, 'confs': confs, 
		'coord': coord, 'proid': proid,
		'areas': areas, 'upleft': upleft, 
		'botright': botright
	}

	return inp_feed_val, loss_feed_val

def shuffle():
	batch_size = cfg.batch_size
	data = parse()
	size = len(data)
	print('Dataset of {} instance(s)'.format(size))
	if batch_size > size: 
		# 전체데이터가 Batch Size 보다 적을때를 대비하여
		cfg.batch_size = batch_size = size
	batch_per_epoch = int(size/batch_size)

	for i in range(cfg.epochs):
		shuffle_idx = perm(np.arange(size))
		# print("shuffle index : ", shuffle_idx)
		for b in range(batch_per_epoch):
			# yield these
			x_batch = list()
			feed_batch = dict()

			for j in range(b*batch_size, b*batch_size + batch_size):
				train_instance = data[shuffle_idx[j]]
				inp, new_feed = _batch(train_instance)

				if inp is None: continue
				x_batch += [np.expand_dims(inp, 0)] # inp.shape : 448, 448, 3
				for key in new_feed:
					new = new_feed[key]
					old_feed = feed_batch.get(key, np.zeros((0,)+new.shape))
					feed_batch[key] = np.concatenate([old_feed, [new]])
			# print("feed_batch : ", len(feed_batch), feed_batch['botright'].shape) # feed_batch :  7 (32, 49, 2, 2)
			# print("x_batch[0].shape : ", x_batch[0].shape) # x_batch.shape :  (1, 448, 448, 3)
			
			x_batch = np.concatenate(x_batch, 0)
			yield x_batch, feed_batch

		print('Finish {} epoch'.format(i+1))

def test_shuffle():
	batch_size = cfg.batch_size
	test_data = pascal_voc_clean_xml(cfg.test_ann_location, cfg.classes_name, False)
	test_size = len(test_data)
	print("Test Dataset of {} instance(s)".format(test_size))

	shuffle_idx = perm(np.arange(test_size))
	print("Test shuffle index : ", shuffle_idx[0:10])
	x_batch = list()
	feed_batch = dict()

	for j in range(batch_size):
		test_instance = test_data[shuffle_idx[j]]
		inp, new_feed = _batch(test_instance, is_test=True)

		if inp is None: continue
		x_batch += [np.expand_dims(inp, 0)]
		for key in new_feed:
			new = new_feed[key]
			old_feed = feed_batch.get(key, np.zeros((0,)+new.shape))
			feed_batch[key] = np.concatenate([old_feed, [new]])
	x_batch = np.concatenate(x_batch, 0)
	return x_batch, feed_batch

if __name__ == '__main__':
	print("hello")