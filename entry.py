#!/usr/bin/python3
from argparse import ArgumentParser
import logging
import os
import sys
from decouple import config
from aerialist.px4.drone_test import DroneTest, AgentConfig, DroneTestResult
from aerialist.px4.docker_agent import DockerAgent
from aerialist.px4.k8s_agent import K8sAgent
from aerialist.px4.local_agent import LocalAgent
from log_generator import log_csv, log_threshold_limit

logger = logging.getLogger(__name__)


def arg_parse():
    main_parser = ArgumentParser(
        description="UAV Security Test Bench",
    )
    subparsers = main_parser.add_subparsers()
    parser = subparsers.add_parser(name="exec", description="generate tests")
    parser.add_argument("--test", default=None, help="test description yaml file")


    parser.add_argument(
        "--agent",
        default=config("AGENT", default="local"),
        choices=["local", "docker", "k8s"],
        help="where to run the tests",
    )
    parser.add_argument(
        "-n",
        default=1,
        type=int,
        help="no. of parallel runs (in k8s)",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="cloud output path to copy logs (in k8s)",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="k8s job id",
    )

    parser.set_defaults(func=run_experiment)
    args = main_parser.parse_args()
    return args


def config_loggers():
    os.makedirs("logs/", exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        filename="logs/root.txt",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler("logs/lib.txt")
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    px4 = logging.getLogger("px4")
    main = logging.getLogger("__main__")
    entry = logging.getLogger("entry")
    px4.addHandler(c_handler)
    main.addHandler(c_handler)
    entry.addHandler(c_handler)
    px4.addHandler(f_handler)
    main.addHandler(f_handler)
    entry.addHandler(f_handler)

def run_experiment(args):
    if args.test is not None:
        test = DroneTest.from_yaml(args.test)
        if test.agent is None:
            test.agent = AgentConfig(
                engine=args.agent,
                count=args.n,
                path=args.path,
                id=args.id,
            )
    
    test_results = execute_test(test)
    logger.info(f"LOG:{test_results[0].log_file}")
    DroneTest.plot(test, test_results)
    create_log_files(test,test_results)

def create_log_files(test: DroneTest, results: DroneTestResult):
    if results is not None and len(results) >= 1:
         for r in results:
            result = [r]
            log_threshold_limit(result, test.agent.path)
            log_csv(test=test,
                    results=result,
                    wind=test.simulation.wind,
                    light=test.simulation.light,
                    obstacles=None
                    if test.simulation is None
                    else test.simulation.obstacles)

def execute_test(test: DroneTest):
    logger.info("setting up the test environment...")
    if test.agent.engine == AgentConfig.LOCAL:
        agent = LocalAgent(test)
    if test.agent.engine == AgentConfig.DOCKER:
        agent = DockerAgent(test)
    if test.agent.engine == AgentConfig.K8S:
        agent = K8sAgent(test)

    logger.info("running the test...")
    test_results = agent.run()

    logger.info("test finished...")
    return test_results

def main():
    try:
        config_loggers()
        args = arg_parse()
        logger.info(f"preparing the test ...{args}")
        args.func(args)

    except Exception as e:
        logger.exception("program terminated:" + str(e), exc_info=True)
        sys.exit(1)



if __name__ == "__main__":
    main()