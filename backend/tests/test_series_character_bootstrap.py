from fastapi.testclient import TestClient

from backend.app import app
from backend.models import AnalyzeSeriesCharactersResponse, CharacterCandidate


def _build_analysis_response() -> AnalyzeSeriesCharactersResponse:
    return AnalyzeSeriesCharactersResponse(
        recommended_main_characters=[
            CharacterCandidate(
                character_name="妻子",
                series_role="核心主角",
                core_identity="喜欢追问情感确认、反应快、带一点误会体质的伴侣角色",
                visual_profile="居家穿着，眼神直接，情绪起伏明显",
                personality_profile="敏感、会追问、容易顺着话头误解",
                speech_style="追问式、带情绪波动",
                relationship_to_others="和丈夫构成稳定的日常反差",
                signature_elements=["抱枕"],
                character_prompt="固定主角：妻子，居家穿着，情绪明显，黑白喜剧漫画风。",
                confidence_reason="她直接推动误会升级，是核心冲突发起者。",
            ),
            CharacterCandidate(
                character_name="丈夫",
                series_role="核心主角",
                core_identity="嘴上会哄人、但经常说出让人误会的比喻型伴侣角色",
                visual_profile="居家短袖，神情轻松，常带无辜表情",
                personality_profile="嘴快、爱打比喻、容易把包袱抛给自己",
                speech_style="轻飘飘接话，最后补刀解释",
                relationship_to_others="和妻子形成稳定的一问一答关系",
                signature_elements=["马克杯"],
                character_prompt="固定主角：丈夫，居家短袖，无辜表情，黑白喜剧漫画风。",
                confidence_reason="他承担误导和包袱落点，是另一位核心主角。",
            ),
        ],
        temporary_characters=[
            CharacterCandidate(
                character_name="店员",
                series_role="临时角色",
                core_identity="只在这一幕短暂出现的服务角色",
                visual_profile="围裙，端着奶茶",
                personality_profile="功能性强",
                speech_style="台词短",
                relationship_to_others="只服务当前场景",
                signature_elements=["奶茶托盘"],
                character_prompt="临时角色：店员，围裙，端奶茶，黑白喜剧漫画风。",
                confidence_reason="一次性功能位，应留在临时角色区。",
            )
        ],
        analysis_notes=["LLM 已根据文案提取具体角色关系。"],
    )


def test_analyze_series_characters_response_shape(monkeypatch):
    monkeypatch.setattr("backend.app.analyze_series_characters", lambda source_text, series_name='': _build_analysis_response())
    client = TestClient(app)

    response = client.post(
        "/api/analyze-series-characters",
        json={"source_text": "美女产品经理天天追着屌丝程序员改需求。"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "recommended_main_characters" in body
    assert "temporary_characters" in body
    assert 2 <= len(body["recommended_main_characters"]) <= 4


def test_analyze_series_characters_prioritizes_two_core_characters():
    from backend.agents.series_characters import _finalize_analysis_result

    response = _finalize_analysis_result(
        _build_analysis_response(),
        "妻子：老公，你说我是你的什么？丈夫：你是我的优乐美啊。",
        "",
    )

    assert len(response.recommended_main_characters) == 2


def test_analyze_series_characters_route_returns_503_without_llm(monkeypatch):
    monkeypatch.setattr("backend.agents.series_characters._should_use_llm", lambda: False)
    client = TestClient(app)

    response = client.post(
        "/api/analyze-series-characters",
        json={"source_text": "妻子：老公，你说我是你的什么？丈夫：你是我的优乐美啊。"},
    )

    assert response.status_code == 503
    assert "LLM" in response.text


def test_analyze_series_characters_rejects_empty_text():
    client = TestClient(app)

    response = client.post("/api/analyze-series-characters", json={"source_text": ""})

    assert response.status_code == 422


def test_analyze_series_characters_sends_tooling_roles_to_temporary_bucket():
    from backend.agents.series_characters import _finalize_analysis_result

    result = _finalize_analysis_result(
        AnalyzeSeriesCharactersResponse(
            recommended_main_characters=[
                CharacterCandidate(
                    character_name="美女产品经理",
                    series_role="核心主角",
                    core_identity="持续追更的产品经理",
                    visual_profile="西装，手拿需求文档",
                    personality_profile="强推进",
                    speech_style="短句追问",
                    relationship_to_others="长期追着程序员改需求",
                    signature_elements=["需求文档"],
                    character_prompt="固定主角：美女产品经理，黑白喜剧漫画风。",
                    confidence_reason="她承担系列冲突推进。",
                ),
                CharacterCandidate(
                    character_name="屌丝程序员",
                    series_role="核心主角",
                    core_identity="被需求追着跑的程序员",
                    visual_profile="格子衬衫，黑眼圈",
                    personality_profile="被动防守",
                    speech_style="先解释再吐槽",
                    relationship_to_others="长期被产品经理催更",
                    signature_elements=["笔记本电脑"],
                    character_prompt="固定主角：屌丝程序员，黑白喜剧漫画风。",
                    confidence_reason="他承担反差和包袱落点。",
                ),
                CharacterCandidate(
                    character_name="前台",
                    series_role="核心主角",
                    core_identity="送咖啡的办公室角色",
                    visual_profile="职业装，端着咖啡",
                    personality_profile="功能性强",
                    speech_style="台词很少",
                    relationship_to_others="只在当前场景短暂出现",
                    signature_elements=["咖啡"],
                    character_prompt="前台角色提示词。",
                    confidence_reason="一次性工具角色。",
                ),
            ],
            temporary_characters=[],
            analysis_notes=["LLM 给出了角色结果。"],
        ),
        "美女产品经理天天追着屌丝程序员改需求，前台顺手给他们送了两杯咖啡。",
        "",
    )

    recommended_names = {
        candidate.character_name for candidate in result.recommended_main_characters
    }
    temporary_names = {
        candidate.character_name for candidate in result.temporary_characters
    }

    assert "前台" not in recommended_names
    assert "前台" in temporary_names


def test_analyze_series_characters_prefers_llm_output_when_available(monkeypatch):
    from backend.agents.series_characters import analyze_series_characters

    monkeypatch.setattr("backend.agents.series_characters._should_use_llm", lambda: True)

    monkeypatch.setattr(
        "backend.agents.series_characters._run_llm_character_analysis",
        lambda source_text, series_name='': _build_analysis_response(),
    )

    result = analyze_series_characters(
        "妻子：老公，你说我是你的什么？丈夫：你是我的优乐美啊。妻子：原来我只是奶茶？丈夫：这样我就可以把你捧在手心里。",
    )

    assert [candidate.character_name for candidate in result.recommended_main_characters] == [
        "妻子",
        "丈夫",
    ]
    assert result.analysis_notes[0] == "LLM 已根据文案提取具体角色关系。"
    assert any("默认优先保留 2 个核心主角" in note for note in result.analysis_notes)
