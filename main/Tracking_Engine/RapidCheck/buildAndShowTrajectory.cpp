#include "tracking_utils.h"
#include "similarity_utils.h"
#include "RCTrajectory.h"

using namespace cv;
using namespace rc;


void buildTrajectory(vector<Segment>& segments, vector<RCTrajectory>& trajectories)
{

	// build Trajectory
	vector<RCTrajectory> trajectoriesStillBeingTracked;
	
	// build trajectories if use online tracking
	for (int segmentNum = 0; segmentNum < segments.size(); segmentNum++)
	{
		Segment& segment = segments[segmentNum];
		vector<tracklet>& curSegmentTracklets = segment.getTracklets();
		if (DEBUG)
			printf("segmentNum : %d, # of tracklets : %d\n", segmentNum, curSegmentTracklets.size());

		// move trajectories finished from trajectoriesStillBeingTracked to trajectoriesFinished
		for (vector<RCTrajectory>::iterator itTrajectories = trajectoriesStillBeingTracked.begin(); itTrajectories != trajectoriesStillBeingTracked.end();)
		{
			RCTrajectory& curTrajectory = *itTrajectories;
			int diffSegmentNum = segmentNum - curTrajectory.getEndSegmentNum();
			// if trajectory is finished
			if (diffSegmentNum > MAXIMUM_LOST_SEGMENTS)
			{
				trajectories.push_back(*itTrajectories);
				itTrajectories = trajectoriesStillBeingTracked.erase(itTrajectories);
				continue;
			}
			else
			{
				itTrajectories++;
			}
		}

		// bipartite graph from i to j
		vector<vector<double> > graphSimilarity = vector<vector<double> >(trajectoriesStillBeingTracked.size(), vector<double>(curSegmentTracklets.size(), 0.0));
		for (int i = 0; i < trajectoriesStillBeingTracked.size(); i++)
		{
			for (int j = 0; j < curSegmentTracklets.size(); j++)
			{
				RCTrajectory& curTrajectory = trajectoriesStillBeingTracked[i];
				tracklet &curTracklet = curTrajectory.getTargets(), &nextTracklet = curSegmentTracklets[j];
				int diffSegmentNum = segmentNum - curTrajectory.getEndSegmentNum();
				if (isValidMotion(curTracklet, nextTracklet, diffSegmentNum))
				{
					double similarity = calcSimilarity(curTracklet, nextTracklet, diffSegmentNum);
					
					if (similarity > TRAJECTORY_MATCH_SIMILARITY_THRES)
						graphSimilarity[i][j] = similarity;
					if (DEBUG)
						printf("%.2lf ", graphSimilarity[i][j]);
				}
				
			}
			if (DEBUG)
				printf("\n");
		}
		if (DEBUG)
			printf("\n");
		vector<bool> mergedNextTracket(curSegmentTracklets.size(), false);
		while (true)
		{
			double maxSimilarity = 0.0;
			int curMaxIdx = -1, nextMaxIdx = -1;
			for (int curIdx = 0; curIdx < graphSimilarity.size(); curIdx++)
			{
				for (int nextIdx = 0; nextIdx < graphSimilarity[curIdx].size(); nextIdx++)
				{
					if (maxSimilarity < graphSimilarity[curIdx][nextIdx])
					{
						maxSimilarity = graphSimilarity[curIdx][nextIdx];
						curMaxIdx = curIdx;
						nextMaxIdx = nextIdx;
					}
				}
			}
			if (maxSimilarity < TRAJECTORY_MATCH_SIMILARITY_THRES)
				break;

			// merge
			RCTrajectory& curTrajectory = trajectoriesStillBeingTracked[curMaxIdx];
			tracklet &nextTracklet = curSegmentTracklets[nextMaxIdx];
			int diffSegmentNum = segmentNum - curTrajectory.getEndSegmentNum();
			if (diffSegmentNum == 1)
			{
				curTrajectory.merge(nextTracklet);
			}
			else
			{
				curTrajectory.mergeWithSegmentGap(nextTracklet, diffSegmentNum);
			}

			// remove similarities
			mergedNextTracket[nextMaxIdx] = true;
			for (int i = 0; i < graphSimilarity.size(); i++)
				graphSimilarity[i][nextMaxIdx] = 0.0;
			for (int j = 0; j < graphSimilarity[curMaxIdx].size(); j++)
				graphSimilarity[curMaxIdx][j] = 0.0;
		}

		for (int trackletNum = 0; trackletNum < curSegmentTracklets.size(); trackletNum++)
		{
			if (!mergedNextTracket[trackletNum])
			{
				trajectoriesStillBeingTracked.push_back(RCTrajectory(curSegmentTracklets[trackletNum], segmentNum));
			}
		}

	}
	for (vector<RCTrajectory>::iterator itTrajectories = trajectoriesStillBeingTracked.begin(); itTrajectories != trajectoriesStillBeingTracked.end(); itTrajectories++)
	{
		trajectories.push_back(*itTrajectories);
	}
}

/**
	Build trajectories of all segements and then, show trace of tracklets

	@param app frame reader with basic parameters set
*/
void buildAndShowTrajectory()
{
	// set input video
	VideoCapture cap(filepath);

	// build target detected frames
	vector<Frame> framePedestrians, frameCars;
	clock_t t = clock();
	if (SELECT_DETECTION_RESPONSE)
	{
		readTargets(cap, framePedestrians, frameCars);
	}
	else
	{
		detectTargets(cap, framePedestrians);
		// detectAndInsertResultIntoDB(cap);
	}
	t = clock() - t;
	if (DEBUG)
		printf("Detection takes %d(ms)\n", t);
	
	// build all tracklets
	t = clock();
	vector<Segment> segmentPedestrians, segmentCars;
	buildTracklets(frameCars, segmentCars, 0);
	buildTracklets(framePedestrians, segmentPedestrians, 1);
	t = clock() - t;
	if (DEBUG)
		printf("Tracklet takes %d(ms)\n", t);

	// build trajectories
	t = clock();
	vector<RCTrajectory> trajectoryPedestrians, trajectoryCars;
	buildTrajectory(segmentPedestrians, trajectoryPedestrians);
	buildTrajectory(segmentCars, trajectoryCars);
	t = clock() - t;
	//if (DEBUG)
		printf("Trajectory takes %d(ms)\n", t);
	
	// insert into DB
	if (INSERT_TRACKING_INTO_DB)
	{
		insertTrackingIntoDB(trajectoryPedestrians, trajectoryCars);
	}
	if (INSERT_OBJECT_INFO_INTO_DB)
	{
		insertObjectInfoIntoDB(trajectoryPedestrians, trajectoryCars);
	}
		
	// show Trajectory	
	showTrajectory(framePedestrians, frameCars, trajectoryPedestrians, trajectoryCars);
}


void analysisVideo()
{
	// set input video
	VideoCapture cap(filepath);

	int numOfTotalFrames = cap.get(CV_CAP_PROP_FRAME_COUNT);
	if (numOfFrames > numOfTotalFrames)
	{
		numOfFrames = numOfTotalFrames;
		endFrameNum = frameStep * numOfFrames + startFrameNum;
	}

	// build target detected frames
	vector<Frame> framePedestrians, frameCars;
	readTargets(cap, framePedestrians, frameCars);
	
	// build all tracklets
	vector<Segment> segmentPedestrians, segmentCars;
	buildTracklets(frameCars, segmentCars, 0);
	buildTracklets(framePedestrians, segmentPedestrians, 1);

	// build trajectories
	vector<RCTrajectory> trajectoryPedestrians, trajectoryCars;
	buildTrajectory(segmentPedestrians, trajectoryPedestrians);
	buildTrajectory(segmentCars, trajectoryCars);

	// insert into DB
	insertTrackingIntoDB(trajectoryPedestrians, trajectoryCars);
	insertObjectInfoIntoDB(trajectoryPedestrians, trajectoryCars);
	if (PRINT_PROGRESS)
		printf("RapidCheck_Tracking %d\n", 100);
}