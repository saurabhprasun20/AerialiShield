from aerialist.px4.file_helper import upload
from aerialist.px4.file_helper import create_dir
from decouple import config
from aerialist.px4.trajectory import Trajectory
from datetime import datetime
import csv
from aerialist.px4.drone_test import DroneTest, AgentConfig, DroneTestResult
from typing import List
from aerialist.px4.obstacle import Obstacle


def log_threshold_limit(results: List[DroneTestResult], upload_dir: str):
    result_dir = config("RESULTS_DIR", default="results/")
    threshold_file = config("THRESHOLD_FILE", default="threshold")
    file_extension = config("FILE_EXTENSION", default=".csv")
    threshold_file_edit_mode = config("THRESHOLD_FILE_EDIT_MODE", default="a")
    file_ts = str(datetime.now().strftime("%Y%m%d%H%M%S"))
    average_traj = Trajectory.average([r.record for r in results])
    distance_list = [r.record.distance(average_traj) for r in results]
    threshold_file_combined = threshold_file + file_ts + file_extension
    f = open(result_dir + threshold_file_combined, threshold_file_edit_mode)
    writer = csv.writer(f)
    writer.writerow(distance_list)
    f.close()
    if upload_dir is not None:
        upload(result_dir + threshold_file_combined, upload_dir)


def log_csv(
        test: DroneTest,
        results: List[DroneTestResult],
        wind: int = 0,
        obstacles: List[Obstacle] = None,
        light: float = 0.4,
        ) -> None:
    result_dir = config("RESULTS_DIR", default="results/")
    dataset_file_combined = config("DATASET_FILE", default="dataset_file_combined")
    dataset_file_edit_mode = config("DATA_FILE_EDIT_MODE", default="a")
    cpu_file = config("CPU_FILE", default="cpu_file")
    cpu_file_edit_mode = config("CPU_FILE_EDIT_MODE", default="a")
    file_extension = config("FILE_EXTENSION", default=".csv")
    default_separation = config("DEFAULT_SEPARATION", default=",")
    file_ts = str(datetime.now().strftime("%Y%m%d%H%M%S"))
    dataset_file = ""
    # print(f"***LOG:{results[0].log_file}")
    log = pyulog.ULog(results[0].log_file)
    # print("**Printing cpu data list")
    cpu_data = log.get_dataset('cpuload')
    # print(cpu_data)
    cpu_load = cpu_data.data['load']
    ram_usage = cpu_data.data['ram_usage']
    cpu_timestamp = cpu_data.data['timestamp']
    cpu_timestamp_list = []
    cpu_header = False
    unsafe_flag = 0
    # print(f'**keys are {cpu_data.data.keys()}')
    # print(f'cpu load and ram usage length are {len(cpu_load)},{len(ram_usage)}')
    for temp_cpu_load, temp_ram_usage, temp_cpu_timestamp in zip_longest(cpu_load, ram_usage, cpu_timestamp):
        cpu_row = [temp_cpu_timestamp, temp_cpu_load, temp_ram_usage]
        cpu_timestamp_list.append(temp_cpu_timestamp)
        f = open(result_dir + cpu_file + "_" + file_ts + file_extension + str(random.randrange(0,100)),
                    cpu_file_edit_mode)
        writer = csv.writer(f)
        if not cpu_header:
            writer.writerow(["timestamp", "cpu_usage", "ram_usage"])
            cpu_header = True
        writer.writerow(cpu_row)
        f.close()

    trajectories: List[Trajectory] = [r.record for r in results]
    for trajectory in trajectories:
        positions = trajectory.positions
        obstacle_flag = False
        obstacles_present = 0
        obstacle_list = []
        # number_of_obstacles = -1
        number_of_trees = 0
        number_of_apartments = 0
        number_of_boxes = 0
        tree_cumm_list = []
        apt_cumm_list = []
        box_cumm_list = []
        box_min_distance = []
        tree_min_distance = []
        apt_min_distance = []
        obstacle_header_distance = []
        tree_count = apt_count = box_count = 0
        if test.simulation.obstacles is None:
            return
        for obs in test.simulation.obstacles:
            min_distance, returned_list = trajectory.distance_to_obstacles([obs])
            if min_distance < 1.5:
                unsafe_flag = 1
            if obs.shape == "TREE":
                tree_cumm_list.append(returned_list)
                tree_count += 1
                tree_index = "tree_" + str(tree_count) + "_min_distance"
                obstacle_header_distance.append(tree_index)
                tree_min_distance.append(min_distance)
            elif obs.shape == "APARTMENT":
                apt_cumm_list.append(returned_list)
                apt_count += 1
                apartment_index = "apt_" + str(apt_count) + "_min_distance"
                obstacle_header_distance.append(apartment_index)
                apt_min_distance.append(min_distance)
            elif obs.shape == "BOX":
                box_cumm_list.append(returned_list)
                box_count += 1
                box_index = "box_" + str(box_count) + "_min_distance"
                obstacle_header_distance.append(box_index)
                box_min_distance.append(min_distance)

        sum_tree = [sum(elts) for elts in zip(*tree_cumm_list)]
        sum_apt = [sum(elts) for elts in zip(*apt_cumm_list)]
        sum_box = [sum(elts) for elts in zip(*box_cumm_list)]
        avg_tree = [divmod(x, len(tree_cumm_list))[0] for x in sum_tree]
        avg_apt = [divmod(x, len(apt_cumm_list))[0] for x in sum_apt]
        avg_box = [divmod(x, len(box_cumm_list))[0] for x in sum_box]
        i = 0

        csv_header = ["x", "y", "z", "r", "timestamp", "wind", "light",
                        "obstacle_present"]
        csv_header_obstacles = ["no_of_obst", "no_of_boxes", "no_of_trees", "no_of_apt", "avg_dist_boxes",
                                "avg_dist_trees", "avg_dist_apt"]
        csv_header_obst_end = ["obst_details", "unsafe"]
        header_flag = False
        if len(obstacles) > 0:
            obstacle_flag = True
            obstacles_present = 1
            for obstacle in test.simulation.obstacles:
                if obstacle.shape == "TREE":
                    number_of_trees += 1
                elif obstacle.shape == "APARTMENT":
                    number_of_apartments += 1
                elif obstacle.shape == "BOX":
                    number_of_boxes += 1
                obstacle_type = obstacle.shape
                obst_x = obstacle.position.x
                obst_y = obstacle.position.y
                obst_z = obstacle.position.z
                obst_r = obstacle.position.r
                temp_obst_row = (obstacle_type, obst_x, obst_y, obst_z, obst_r)
                obstacle_list.append(temp_obst_row)
        for position in positions:
            x = position.x
            y = position.y
            z = position.z
            r = position.r
            timestamp = position.timestamp
            average_tree_distance = average_box_distance = average_apt_distance = 0

            if len(avg_tree) > 0:
                average_tree_distance = avg_tree[i]
            if len(avg_box) > 0:
                average_box_distance = avg_box[i]
            if len(avg_apt) > 0:
                average_apt_distance = avg_apt[i]
            i += 1
            header_final = []
            if obstacle_flag:
                number_of_obstacles = len(obstacle_list)
                if not header_flag:
                    header_final = csv_header + csv_header_obstacles + obstacle_header_distance + csv_header_obst_end
                row = [x, y, z, r, timestamp, wind, light, obstacles_present, number_of_obstacles, number_of_trees,
                        number_of_boxes,
                        number_of_apartments, average_box_distance, average_tree_distance,
                        average_apt_distance] + tree_min_distance + box_min_distance + apt_min_distance + [
                            obstacle_list] + [unsafe_flag]
            else:
                if not header_flag:
                    header_final = csv_header
                row = [x, y, z, r, timestamp, wind, light, obstacles_present]
            dataset_file = result_dir + dataset_file_combined + "_" + file_ts + file_extension
            f = open(dataset_file, dataset_file_edit_mode)
            write = csv.writer(f)
            if not header_flag:
                write.writerow(header_final)
                header_flag = True
            write.writerow(row)
            f.close()
    if upload_dir is not None:
        upload(dataset_file, test.agent.path)
