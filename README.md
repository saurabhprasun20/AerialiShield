# AERIALSHIELD: UAV SECURITY TEST Bench

<!-- ## [Demo Video](https://youtu.be/pmBspS2EiGg) -->

**AerialiSheild** is a novel security test bench for UAV software that is build on top of the Aerialist. It automates all the necessary UAV testing steps: setting up the test environment, building and running the UAV firmware code, configuring the simulator with the simulated world properties, connecting the simulated UAV to the firmware and applying proper UAV configurations at startup, scheduling and executing runtime commands, monitoring the UAV at runtime for any issues, and extracting the flight log file after the test completion.

AerialSheild aim to provide researchers with a platform to carry out the security attack and find vulnerability in the underlying vision-based algorithm. 


## Getting Started

You can execute UAV Security test cases with AerialShield in two different ways. Soon we will publish the code to run it locally.

- [Docker Test Execution](#docker-test-execution) (**Recommended**): Execute Test Cases in pre-built Docker containers without the need to install PX4 dependencies on your machine.
This is the recommended option for most use cases and supports headless simulation (without the graphical interface).


- [Kubernetes Test Execution](#kubernetes-test-execution): You can also deploy your test execution to a Kubernetes cluster for more scale.
This option is only recommended if you are using Aerialist to conduct large-scale experiments on test generation for drones.

### Docker Test Execution

Using Docker containers with pre-configured PX4 dependencies to execute test cases is the simplest and recommended way of executing UAV tests with Aerialist.
AerialShield Docker image is hosted on [Dockerhub](https://hub.docker.com/r/prasun20/aerialshield).

#### Using Docker Container's CLI

- Requirements: [Docker](https://docs.docker.com/engine/install/)
- This has been tested on **Windows, Ubuntu and macOS with x86-64 processors**.
  - You may need to rebuild the docker image if you are using another OS or architecture.

1. `docker run -it prasun20/aerialshield bash`

- You can now use the [command-line-interface in the container's bash.
- check `python3 entry.py exec --help`


### Kubernetes Test Execution

AerialShield can also deploy test executions on a Kubernetes cluster to facilitate running tests in the cloud. Specifically, as can be seen in the below figure, AerialSheild can run multiple executions of the same test case in isolated Kubernets pods in parallel, and gather test results for further processing. 


## Usage

### Test Description File

You can define the test as below:

```yaml
# template-test.yaml
drone:
  port: sitl 
  params_file: test/mission1-params.csv #csv file with the same structure as above 
  mission_file: test/mission1.plan # input mission file address

simulation:
  simulator: ros # the simulator environment to run {gazebo,jmavsim,ros} 
  speed: 1 # the simulator speed relative to real time
  headless: true # whether to run the simulator headless
    obstacles:
    - size: ## Obstacle's size in l,w,h
        l: 1
        w: 1
        h: 1
      position: # Obstacle's poisition in x,y,z
        x: 4
        y: 8
        z: 0
        angle: 0
      shape: BOX #Obstacle's shape
      pattern_design: chequered #Pattern on obstacles.
    - size:
        l: 0
        w: 0
        h: 0
      position:
        x: 1
        y: 3
        z: 0
        angle: 0
      shape: TREE
    - size:
        l: 20
        w: 22
        h: 14
      position:
        x: 4
        y: 15
        z: 0
        angle: 0
      shape: APARTMENT
  world_file_name: ["simple_obstacle_scenario1"]
test:
  commands_file: samples/flights/mission1-commands.csv # runtime commands file address

assertion:
  log_file: samples/flights/mission1.ulg # reference log file address
  # variable: trajectory # reference variables to compare 

```
For now we have 3 different types of obstacles that we can inject which are apartment, tree and box. Box has additional functionalities. We can add patterns on the boxes like chequered, green or other patterns from a list of given patterns.

Apartment and Trees are of fixed size. So your entered value for size of tress and apartment won't be parsed.


## License

The software we developed is distributed under MIT license. See the [license](./LICENSE.md) file.
