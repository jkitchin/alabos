"""
Define the base class of operation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Type

from bson import ObjectId

from alab_management.device_view import DeviceView
from alab_management.logger import DBLogger
from alab_management.sample_view.sample_view import SampleView


@dataclass
class BaseTask(ABC):
    """
    The abstract class of task.

    All the tasks should inherit from this class.

    Attributes:
        task_id: the identifier of task
        sample_id: the id of sample to do tasks on
    """
    task_id: ObjectId = field(hash=False, compare=False)
    device_view: DeviceView = field(hash=False, compare=False)
    sample_view: SampleView = field(hash=False, compare=False)
    logger: DBLogger = field(hash=False, compare=False)

    @abstractmethod
    def run(self):
        """
        Run the task
        """
        raise NotImplementedError()


_task_registry: Dict[str, Type[BaseTask]] = {}


def add_task(task: Type[BaseTask]):
    """
    Register a task
    """
    if task.__name__ in _task_registry:
        raise KeyError("Duplicated operation name {}".format(task.__name__))
    _task_registry[task.__name__] = task


def get_all_tasks() -> Dict[str, Type[BaseTask]]:
    return _task_registry.copy()
