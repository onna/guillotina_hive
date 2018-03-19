import asyncio
import math

from guillotina.interfaces import IApplication
from guillotina.interfaces import IRequest
from guillotina.utils import get_containers


TESTING_OBJECT = {
    'value': 0
}


async def calculate_numbers(number_one, number_two):
    await asyncio.sleep(0.01)
    result = number_one * number_two
    print("%f" % float(result))
    return result


async def task_with_all_args(request, root):
    assert IRequest.providedBy(request)
    assert IApplication.providedBy(root)


async def slow_task(timeout):
    await asyncio.sleep(timeout)


async def compute(request, root):
    val = 0.0
    async for txn, tm, container in get_containers(request):
        async for key, value in container.async_items():
            number = value.creation_date.timestamp()
            val += number / (number + math.exp(-0.5))
    return val


async def local_memory(number_one):
    TESTING_OBJECT['value'] = number_one
