import asyncio
from time import sleep


def long_sync_task():
    sleep(10)
    return 1


async def long_runner_task():
    print("Long running task finished")


async def counter():
    counter = 0
    try:
        while True:
            print(f"Counter: {counter}")
            await asyncio.sleep(0.1)
            counter += 1
    except Exception as e:
        print(f"Exception {e}")
    finally:
        return counter


async def main():

    tasks = []

    counter_task = asyncio.create_task(counter())
    await asyncio.get_running_loop().run_in_executor(None, long_sync_task)

    print(f"Done waiting for long task")
    counter_task.cancel()
    # print(f"final counter {count}")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
