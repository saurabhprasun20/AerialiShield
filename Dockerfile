FROM aerialist-test:latest
RUN pip3 install -e /src/aerialist/

COPY ./requirements.txt /src/aerialshield/requirements.txt
WORKDIR /src/aerialshield/
RUN pip3 install -r /src/aerialshield/requirements.txt

COPY ./ /src/aerialshield//
RUN mkdir -p ./logs/ ./results/ ./generated_tests/ ./tmp

ENV AGENT local
ENV AVOIDANCE_LAUNCH /src/aerialist/aerialist/resources/simulation/local_planner_stereo.launch
ENV AVOIDANCE_BOX /src/aerialist/aerialist/resources/simulation/box.xacro

WORKDIR /src/catkin_ws/src/avoidance/
RUN catkin_create_pkg intermediate_image_save std_msgs rospy roscpp cv_bridge
WORKDIR /src/catkin_ws/src/avoidance/intermediate_image_save/src
RUN mkdir -p nodes
WORKDIR /src/catkin_ws/src/avoidance/intermediate_image_save/src/nodes
COPY ros_node_script/scripts/ .
RUN catkin build -w /src/catkin_ws &&\
    echo "source /src/catkin_ws/devel/setup.bash" >> ~/.bashrc  
WORKDIR /src/aerialshield/