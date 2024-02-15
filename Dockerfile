FROM skhatiri/aerialist:latest
RUN pip3 install -e /src/aerialist/

COPY ./requirements.txt /src/aerialshield/requirements.txt
WORKDIR /src/aerialshield/
RUN pip3 install -r /src/aerialshield/requirements.txt

COPY ./ /src/aerialshield//
RUN mkdir -p ./logs/ ./results/ ./generated_tests/

ENV AGENT local
ENV AVOIDANCE_LAUNCH /src/aerialist/aerialist/resources/simulation/local_planner_stereo.launch
ENV AVOIDANCE_BOX /src/aerialist/aerialist/resources/simulation/box.xacro

