from aerialist.px4.file_helper import upload
from decouple import config
from aerialist.px4.trajectory import Trajectory
from datetime import datetime
import csv
from itertools import zip_longest
import pyulog
from aerialist.px4.drone_test import DroneTest, DroneTestResult
from typing import List
from aerialist.px4.obstacle import Obstacle
import numpy as np

average_distance_tree = []
average_distance_box = []
avergae_distance_apartment = []
min_distance_tree = []
min_distance_box = []
min_distance_apartment = []
max_distance_tree = []
max_distance_box = []
max_distance_apartment = []


def log_threshold_limit(results: List[DroneTestResult], upload_dir: str):
    print("In the log threshold method")
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
        upload_dir: str = None
) -> None:
    print("In the log_csv method")
    global average_distance_box, average_distance_tree, avergae_distance_apartment, min_distance_apartment, min_distance_box, min_distance_tree, max_distance_apartment, max_distance_box, max_distance_tree
    result_dir = config("RESULTS_DIR", default="results/")
    dataset_file_combined = config("DATASET_FILE", default="dataset_file_combined")
    dataset_file_edit_mode = config("DATA_FILE_EDIT_MODE", default="a")
    cpu_file = config("CPU_FILE", default="cpu_file")
    cpu_file_edit_mode = config("CPU_FILE_EDIT_MODE", default="a")
    file_extension = config("FILE_EXTENSION", default=".csv")
    default_separation = config("DEFAULT_SEPARATION", default=",")
    file_ts = str(datetime.now().strftime("%Y%m%d%H%M%S"))
    print(f"@@Timestamp is {file_ts}")
    dataset_file = ""
    # print(f"***LOG:{results[0].log_file}")
    log = pyulog.ULog(results[0].log_file)
    # print("**Printing cpu data list")
    cpu_data = log.get_dataset('cpuload')
    # print(cpu_data)
    cpu_load = cpu_data.data['load']
    ram_usage = cpu_data.data['ram_usage']
    cpu_timestamp = cpu_data.data['timestamp']
    unsafe_flag = 0

    generate_cpu_usage(test=test, cpu_load=cpu_load, ram_usage=ram_usage, cpu_timestamp=cpu_timestamp, file_ts=file_ts,
                       upload_dir=upload_dir)
    # cpu_timestamp_list = []
    # cpu_header = False
    # # print(f'**keys are {cpu_data.data.keys()}')
    # # print(f'cpu load and ram usage length are {len(cpu_load)},{len(ram_usage)}')
    # cpu_file_name = result_dir + cpu_file + "_" + file_ts + file_extension
    # print(f"%%%%%cpu_file_name is {cpu_file_name}")
    # for temp_cpu_load, temp_ram_usage, temp_cpu_timestamp in zip_longest(cpu_load, ram_usage, cpu_timestamp):
    #     cpu_row = [temp_cpu_timestamp, temp_cpu_load, temp_ram_usage]
    #     cpu_timestamp_list.append(temp_cpu_timestamp)
    #     f = open(cpu_file_name, cpu_file_edit_mode)
    #     writer = csv.writer(f)
    #     if not cpu_header:
    #         writer.writerow(["timestamp", "cpu_usage", "ram_usage"])
    #         cpu_header = True
    #     writer.writerow(cpu_row)
    #     f.close()

    # if upload_dir is not None:
    #     upload(cpu_file_name, test.agent.path)

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
        box_max_distance = []
        tree_max_distance = []
        apt_max_distance = []
        obstacle_header_distance = []
        tree_count = apt_count = box_count = 0
        if test.simulation.obstacles is None:
            return
        for obs in test.simulation.obstacles:
            min_distance, returned_list = trajectory.distance_to_obstacles([obs])
            min_distance_temp, max_distance = trajectory.min_max_dist_to_obstacle([obs])
            if min_distance < 1.5:
                unsafe_flag = 1
            if obs.shape == "TREE":
                tree_cumm_list.append(returned_list)
                tree_count += 1
                tree_index = "tree_" + str(tree_count) + "_min_distance"
                obstacle_header_distance.append(tree_index)
                tree_min_distance.append(min_distance)
                tree_max_distance.append(max_distance)
            elif obs.shape == "APARTMENT":
                apt_cumm_list.append(returned_list)
                apt_count += 1
                apartment_index = "apt_" + str(apt_count) + "_min_distance"
                obstacle_header_distance.append(apartment_index)
                apt_min_distance.append(min_distance)
                apt_max_distance.append(max_distance)
            elif obs.shape == "BOX":
                box_cumm_list.append(returned_list)
                box_count += 1
                box_index = "box_" + str(box_count) + "_min_distance"
                obstacle_header_distance.append(box_index)
                box_min_distance.append(min_distance)
                box_max_distance.append(max_distance)

        sum_tree = [sum(elts) for elts in zip(*tree_cumm_list)]
        sum_apt = [sum(elts) for elts in zip(*apt_cumm_list)]
        sum_box = [sum(elts) for elts in zip(*box_cumm_list)]
        avg_tree = [divmod(x, len(tree_cumm_list))[0] for x in sum_tree]
        avg_apt = [divmod(x, len(apt_cumm_list))[0] for x in sum_apt]
        avg_box = [divmod(x, len(box_cumm_list))[0] for x in sum_box]

        average_distance_box = avg_box
        min_distance_box = box_min_distance
        max_distance_box = box_max_distance
        average_distance_tree = avg_tree
        min_distance_tree = tree_min_distance
        max_distance_tree = tree_max_distance
        avergae_distance_apartment = avg_apt
        min_distance_apartment = apt_min_distance
        max_distance_apartment = apt_max_distance

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

    generate_complexity_matrix(obstacles=obstacles, upload_dir=upload_dir, file_ts=file_ts, path=test.agent.path)


def generate_cpu_usage(test: DroneTest,
                       cpu_load,
                       ram_usage,
                       cpu_timestamp,
                       file_ts,
                       upload_dir) -> None:
    result_dir = config("RESULTS_DIR", default="results/")
    cpu_file = config("CPU_FILE", default="cpu_file")
    cpu_file_edit_mode = config("CPU_FILE_EDIT_MODE", default="a")
    file_extension = config("FILE_EXTENSION", default=".csv")
    cpu_timestamp_list = []
    cpu_header = False
    unsafe_flag = 0
    # print(f'**keys are {cpu_data.data.keys()}')
    # print(f'cpu load and ram usage length are {len(cpu_load)},{len(ram_usage)}')
    cpu_file_name = result_dir + cpu_file + "_" + file_ts + file_extension
    print(f"%%%%% cpu_file_name is {cpu_file_name}")
    for temp_cpu_load, temp_ram_usage, temp_cpu_timestamp in zip_longest(cpu_load, ram_usage, cpu_timestamp):
        cpu_row = [temp_cpu_timestamp, temp_cpu_load, temp_ram_usage]
        cpu_timestamp_list.append(temp_cpu_timestamp)
        f = open(cpu_file_name, cpu_file_edit_mode)
        writer = csv.writer(f)
        if not cpu_header:
            writer.writerow(["timestamp", "cpu_usage", "ram_usage"])
            cpu_header = True
        writer.writerow(cpu_row)
        f.close()

    if upload_dir is not None:
        upload(cpu_file_name, test.agent.path)


def generate_complexity_matrix(
        obstacles: List[Obstacle] = None,
        upload_dir: str = None,
        file_ts: str = None,
        path: str = None
) -> None:
    min_max_apartment_list = []
    min_max_tree_list = []
    min_max_box_list = []
    result_dir = config("RESULTS_DIR", default="results/")
    complexity_file = config("COMPLEXITY_FILE", default="complexity_file")
    complexity_file_edit_mode = config("COMPLEXITY_FILE_EDIT_MODE", default="a")
    file_extension = config("FILE_EXTENSION", default=".csv")
    if len(obstacles) == 0:
        return
    number_of_obstacles = len(obstacles)
    volume_list = []
    point_list = []
    apartment_present = False
    box_present = False
    tree_present = False
    for obstacle in obstacles:
        obst_l = obstacle.size.l
        obst_w = obstacle.size.w
        obst_h = obstacle.size.h
        obst_x = obstacle.position.x
        obst_y = obstacle.position.y
        if obstacle.shape == "APARTMENT":
            apartment_present = True
        if obstacle.shape == "TREE":
            tree_present = True
        if obstacle.shape == "BOX":
            box_present = True

        point_list.append([obst_x, obst_y])
        volume = obst_l * obst_w * obst_h
        volume_list.append(volume)

    average_volume = sum(volume_list) / len(volume_list)
    median_volume_val = np.median(volume_list) 
    min_max_volume_list = min_max_weighted_sum(volume_list, min(volume_list), max(volume_list))
    euclidean_distance_list, average_distance_bw_obs, euclidean_median_value = calculate_euclidean_distances(point_list)
    min_dist_obs, max_dist_obs = find_min_max(euclidean_distance_list)
    print(f'min_dis_obs{min_dist_obs} and max_dist_obs {max_dist_obs}')
    print(f'distance_list {euclidean_distance_list}')
    min_max_distance_list = min_max_weighted_sum(euclidean_distance_list, min_dist_obs, max_dist_obs)
    if apartment_present:
        min_max_apartment_list = min_max_weighted_sum(avergae_distance_apartment, min_distance_apartment[0],
                                                      max_distance_apartment[0])
    if tree_present:
        min_max_tree_list = min_max_weighted_sum(average_distance_tree, min_distance_tree[0], max_distance_tree[0])
    if box_present:
        print("Pront")
        print(min_distance_box[0])
        print(max_distance_box[0])
        min_max_box_list = min_max_weighted_sum(average_distance_box, min_distance_box[0], max_distance_box[0])
    header = False
    complexity_file_name = result_dir + complexity_file + "_" + file_ts + file_extension

    for temp_volume_list, temp_distance_list, temp_apt_list, temp_tree_list, temp_box_list in zip_longest(
            min_max_volume_list, min_max_distance_list, min_max_apartment_list,
            min_max_tree_list, min_max_box_list):
        row_to_write = [number_of_obstacles, volume_list, average_volume, median_volume_val, euclidean_distance_list,
                        average_distance_bw_obs, euclidean_median_value, temp_volume_list, temp_distance_list, temp_apt_list, temp_tree_list,
                        temp_box_list]
        f = open(complexity_file_name, complexity_file_edit_mode)
        writer = csv.writer(f)
        if not header:
            writer.writerow(
                ["No._of_Obst", "volume_elements", "average_volume", "median_val", "distance_obstacles", "euclidean_dist_avg", "euclidean_median_val",
                 "min_max_volume", "min_max_euclidean_dist", "min_max_apt_dist", "min_max_tree_dist",
                 "min_max_box_dist"])
            header = True
        writer.writerow(row_to_write)
        f.close()

    if upload_dir is not None:
        upload(complexity_file_name, path)


def min_max_weighted_sum(elemnts_list, min_val, max_val):
    print(f'elements_list is {elemnts_list}')
    print(f'min_val is {min_val} and nax_val is:{max_val}')
    min_max_weighted_list = []
    for element in elemnts_list:
        if min_val == max_val:
            min_max_weighted_list.append((element - min_val))
        else:
            min_max_weighted_list.append((element - min_val) / (max_val - min_val))
    return min_max_weighted_list


def calculate_euclidean_distances(points):
    num_points = len(points)
    distances = np.zeros((num_points, num_points))

    for i in range(num_points):
        for j in range(i + 1, num_points):
            # Calculate the Euclidean distance and store it in the matrix
            distances[i, j] = np.linalg.norm(np.array(points[i]) - np.array(points[j]))
            distances[j, i] = distances[i, j]  # Mirror the distance for the symmetric matrix

            euclidean_distances = distances[np.tril_indices(num_points, -1)]
            # distance = np.sum(euclidean_distances)
            average_distance = np.mean(euclidean_distances)
            median_value = np.median(euclidean_distances)

    return euclidean_distances, average_distance, median_value


# def find_average_np(point_list):
#     points = np.array(point_list)
#     diff = points[:, np.newaxis, :] - points[np.newaxis, :, :]
#     distances = np.sqrt(np.sum(diff ** 2, axis=-1))
#     total_distance_sum = np.sum(distances)
#     average_distance_obs = total_distance_sum / (distances.shape[0] * distances.shape[1] - distances.shape[0])
#
#     mask = np.ones(distances.shape, dtype=bool)
#     np.fill_diagonal(mask, False)
#     non_diagonal_elements = distances[mask]
#     print(non_diagonal_elements.shape)
#     print(len(non_diagonal_elements))
#
#     return distances, average_distance_obs, non_diagonal_elements


def find_min_max(temp_list):
    min_val = min(temp_list)
    max_val = max(temp_list)
    return min_val, max_val

# def find_min_max(np_array):
#     np.fill_diagonal(np_array, np.inf)
#     min_distance = np.min(np_array)
#     print("Minimum distance (excluding diagonal):", min_distance)
#     np.fill_diagonal(np_array, 0)
#     max_distance = np.max(np_array)
#     print("Maximum distance:", max_distance)
#     return min_distance,max_distance
