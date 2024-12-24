# Асинхронный режим
from asyncio import run, gather, create_task, all_tasks, current_task

from aiohttp import ClientSession

import datetime
from math import ceil

from models import engine, Session, Base, SwapiPeople

URL = 'https://swapi.dev/api/people/'

async def swapi_json(client, *args, **kwargs):
    async with client.get(*args, **kwargs) as response:
        json_data = await response.json()
        return json_data


async def page_param():
    async with ClientSession() as client:
        data = await swapi_json(client, URL)
        persons_on_page = len(data['results'])
        all_persons = data['count']
        all_pages = ceil(all_persons / persons_on_page)
        return all_pages, persons_on_page


async def get_list(client, field: str, *links):
    if not links:
        return
    coroutines = [swapi_json(client, link) for link in links]
    jsons = await gather(*coroutines)
    text = ', '.join(swapi_data[field] for swapi_data in jsons)
    return text


async def get_person_data(client, person, id_):
    advanced = await gather(get_list(client, 'name', person['homeworld']),
                              get_list(client, 'title', *person['films']),
                              get_list(client, 'name', *person['species']),
                              get_list(client, 'name', *person['starships']),
                              get_list(client, 'name', *person['vehicles']))
    person_data = dict(id=id_,
                       birth_year=person['birth_year'],
                       eye_color=person['eye_color'],
                       gender=person['gender'],
                       hair_color=person['hair_color'],
                       height=person['height'],
                       mass=person['mass'],
                       name=person['name'],
                       skin_color=person['skin_color'],
                       homeworld=advanced[0],
                       films=advanced[1],
                       species=advanced[2],
                       starships=advanced[3],
                       vehicles=advanced[4])
    return person_data


PAGES_NUMBER, PERSONS_ON_PAGE = run(page_param())


async def get_persons_on_page(client, page: int):
    params = {'page': page}
    start = (page * PERSONS_ON_PAGE) - (PERSONS_ON_PAGE - 1)
    response = await swapi_json(client, URL, params=params)
    persons = [
        await get_person_data(client, person, id_)
        for id_, person in enumerate(response['results'],
                                     start=start)
    ]
    return persons


async def first_migrate():
    async with engine.begin() as connect:
        await connect.run_sync(Base.metadata.drop_all)
        await connect.run_sync(Base.metadata.create_all)


async def get_people():
    await first_migrate()

    async with ClientSession() as client:
        for page in range(1, PAGES_NUMBER + 1):
            person_coros = get_persons_on_page(client, page)
            paste_to_db_coro = paste_to_db(person_coros)
            create_task(paste_to_db_coro)

    tasks_for_shutdown = all_tasks() - {current_task(), }
    for task in tasks_for_shutdown:
        await task

    await engine.dispose()


async def paste_to_db(coros):
    jsons = await coros
    async with Session() as session:
        orm_objects = [SwapiPeople(**json_) for json_ in jsons]
        session.add_all(orm_objects)
        await session.commit()


if __name__ == '__main__':
    start = datetime.datetime.now()
    run(get_people())
    print(datetime.datetime.now() - start)