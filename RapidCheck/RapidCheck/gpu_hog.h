#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <iomanip>
#include <stdexcept>
#include <opencv2/core/utility.hpp>
#include "opencv2/cudaobjdetect.hpp"
#include "opencv2/highgui.hpp"
#include "opencv2/objdetect.hpp"
#include "opencv2/imgproc.hpp"

using namespace std;
using namespace cv;

class Args
{
public:
	Args();
	static Args read(int argc, char** argv);

	string src;
	bool src_is_folder;
	bool src_is_video;
	bool src_is_camera;
	int camera_id;

	bool svm_load;
	string svm;

	bool write_video;
	string dst_video;
	double dst_video_fps;

	bool make_gray;

	bool resize_src;
	int width, height;

	double scale;
	int nlevels;
	int gr_threshold;

	double hit_threshold;
	bool hit_threshold_auto;

	int win_width;
	int win_stride_width, win_stride_height;
	int block_width;
	int block_stride_width, block_stride_height;
	int cell_width;
	int nbins;

	bool gamma_corr;
};


class App
{
public:
	App(const Args& s);
	void run();

	void handleKey(char key);

	void hogWorkBegin();
	void hogWorkEnd();
	string hogWorkFps() const;

	void workBegin();
	void workEnd();
	string workFps() const;

	string message() const;

private:
	App operator=(App&);

	Args args;
	bool running;

	bool use_gpu;
	bool make_gray;
	double scale;
	int gr_threshold;
	int nlevels;
	double hit_threshold;
	bool gamma_corr;

	int64 hog_work_begin;
	double hog_work_fps;

	int64 work_begin;
	double work_fps;
};
