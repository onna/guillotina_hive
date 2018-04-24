import json


async def test_dequeuefolder(hive_requester):
    async with hive_requester as requester:
        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks',
            data=json.dumps({
                "@type": "Task",
                "id": "task1"
            })
        )
        assert status == 500

        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks',
            data=json.dumps({
                "@type": "Task",
                "id": "calculate-numbers",
                "max_len": 1
            })
        )

        assert status == 201

        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks/calculate-numbers',
            data=json.dumps({
                "@type": "Execution",
                "id": "execution1"
            })
        )
        assert status == 201

        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks/calculate-numbers',
            data=json.dumps({
                "@type": "Execution",
                "id": "execution2"
            })
        )
        assert status == 201

        resp, status = await requester(
            'POST',
            '/db/guillotina/+tasks/calculate-numbers',
            data=json.dumps({
                "@type": "Execution",
                "id": "execution3"
            })
        )
        assert status == 201

        resp, status = await requester(
            'GET',
            '/db/guillotina/+tasks/calculate-numbers/@ids'
        )
        assert status == 200
        assert len(resp) == 1
        assert 'execution1' not in resp
        assert 'execution2' not in resp
