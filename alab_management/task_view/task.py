"""
Define the base class of task, which will be used for defining more tasks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, TYPE_CHECKING

from bson import ObjectId

if TYPE_CHECKING:
    from ..lab_view import LabView


class BaseTask(ABC):
    """
    The abstract class of task.

    All the tasks should inherit from this class.
    """

    def __init__(self, task_id: ObjectId, lab_view: "LabView", sub_task_id: str = ""):
        """
        Args:
            task_id: the identifier of task
            sub_task_id: a string that indicate the parent_task

        Here is an example about how to define a custom task

        .. code-block:: python

          def __init__(self, sample_1: ObjectId, sample_2: Optional[ObjectId],
                       sample_3: Optional[ObjectId], sample_4: Optional[ObjectId],
                        setpoints: List[Tuple[float, float]], *args, **kwargs):
              super(Heating, self).__init__(*args, **kwargs)
              self.setpoints = setpoints
              self.samples = [sample_1, sample_2, sample_3, sample_4]
        """
        self.task_id = task_id
        self.sub_task_id: str = sub_task_id
        self.child_task_num: int = 0
        self.lab_view = lab_view
        self.logger = self.lab_view.logger

    @abstractmethod
    def run(self):
        """
        Run the task. In this function, you can request lab resources from lab manager and log data to database
        with logger.

        ``request_resources`` will not return until all the requested resources are available. So the task will
        pend until it gets the requested resources, which prevent the conflict in the resource allocation.

        When a device get the requested device and sample positions, it also takes over the ownership of these
        resources, i.e., other task cannot use the device or request the sample positions this task has requested.

        We use a context manager to manage the ownership of the resources. when a task is completed, all the devices
        and sample positions will be released automatically.

        Here is an example about how to define the task

        .. code-block:: python

          # request devices and sample positions from lab manager. The `$` represents
          # the name of assigned devices in the sample positions we try to request,
          # 4 is the number of sample positions.
          with self.lab_view.request_resources({Furnace: [("$.inside", 4)]}) as devices_and_positions:
              devices, sample_positions = devices_and_positions
              furnace = devices[Furnace]
              inside_furnace = sample_positions[Furnace]["$.inside"]

              for sample in self.samples:
                  # in a task, we can call other tasks, which will share the same
                  # task id, requested devices and sample positions.
                  moving_task = Moving(sample=sample,
                                       task_id=self.task_id,
                                       dest=inside_furnace[0],
                                       lab_view=self.lab_view,
                                       logger=self.logger)
                  moving_task.run()

              # send command to device
              furnace.run_program(self.setpoints)

              while furnace.is_running():
                  # log the device data, which is current temperature of the furnace
                  self.logger.log_device_signal({
                      "device": furnace.name,
                      "temperature": furnace.get_temperature(),
                  })

        """
        raise NotImplementedError()

    def get_one_child_sub_task_id(self):
        child_id = f"{self.sub_task_id}.{self.child_task_num}"
        self.child_task_num += 1
        return child_id

    def create_sub_task(self, task_type: Type["BaseTask"], *args, **kwargs) -> "BaseTask":
        """
        Create subtask by task_type
        """
        return task_type(task_id=self.task_id, lab_view=self.lab_view,
                         sub_task_id=self.get_one_child_sub_task_id(), *args, **kwargs)


_task_registry: Dict[str, Type[BaseTask]] = {}


def add_task(task: Type[BaseTask]):
    """
    Register a task
    """
    if task.__name__ in _task_registry:
        raise KeyError(f"Duplicated operation name {task.__name__}")
    _task_registry[task.__name__] = task


def get_all_tasks() -> Dict[str, Type[BaseTask]]:
    """
    Get all the tasks in the registry
    """
    return _task_registry.copy()
