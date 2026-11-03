import asyncio
import json
import pytest
import httpx

@pytest.mark.asyncio
async def test_live_streaming_and_vote():
    async with httpx.AsyncClient(timeout=90.0) as client:
        # 1. Create battle
        resp = await client.post(
            "http://localhost:8000/api/battles",
            json={"prompt": "What is quantum physics in one sentence?"},
        )
        assert resp.status_code == 201
        data = resp.json()
        battle_id = data["battle_id"]
        category = data["category"]
        print(f"\n[E2E] Battle created: {battle_id} (category: {category})")

        # 2. Concurrently stream Slot A and Slot B
        async def read_stream(slot: str):
            tokens = []
            async with client.stream("GET", f"http://localhost:8000/api/battles/{battle_id}/stream/{slot}") as r:
                assert r.status_code == 200
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        payload = line[6:]
                        try:
                            d = json.loads(payload)
                            if "token" in d:
                                tokens.append(d["token"])
                        except Exception:
                            pass
            text = "".join(tokens)
            print(f"[E2E] Slot {slot} received {len(tokens)} tokens ({len(text)} chars)")
            return text

        t_a, t_b = await asyncio.gather(read_stream("A"), read_stream("B"))
        assert len(t_a) > 0, "Slot A received no tokens!"
        assert len(t_b) > 0, "Slot B received no tokens!"

        # 3. Vote on Slot A
        await asyncio.sleep(2.0)
        vote_resp = await client.post(
            f"http://localhost:8000/api/battles/{battle_id}/vote",
            json={"choice": "A", "time_to_vote_ms": 2500},
        )
        assert vote_resp.status_code == 200
        vote_data = vote_resp.json()
        assert vote_data["choice"] == "A"
        assert len(vote_data["responses"]) == 2
        for r in vote_data["responses"]:
            print(f"[E2E] Reveal Slot {r['slot']}: {r['model_name']} ({r['model_slug']}) - {r['output_tokens']} tokens, latency: {r['total_latency_ms']}ms")

