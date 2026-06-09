from fastapi.testclient import TestClient

from backend.agents.joke_to_comic import build_prompt_pack, normalize_model_name
from backend.app import app
from backend.models import ComicPlan, ComicPlanPanel


def test_normalize_model_name_strips_provider_prefix():
    assert normalize_model_name("openai:gpt-5.4") == "gpt-5.4"
    assert normalize_model_name("gpt-5.4") == "gpt-5.4"


def test_joke_to_comic_returns_prompt_pack_structure(monkeypatch):
    fake_pack = {
        "title": "程序员相亲",
        "source_joke": "程序员去相亲，对方问他有没有房，他说 GitHub 上有好几套。",
        "format": {
            "panel_count": 4,
            "image_width": 1080,
            "image_height": 1440,
            "page_layout": "2x2",
        },
        "story_summary": "把房产误会改成四格节奏清楚的相亲笑话。",
        "humor_explanation": "笑点来自把仓库误听成房子，最后一格再揭晓真正含义。",
        "negative_prompt": "模糊，低清晰度，坏手，水印，标志",
        "generation_notes": [
            "四格里的人物和服装保持一致。",
            "节奏要一路推进到最后一格包袱。",
        ],
        "panels": [
            {
                "panel_number": 1,
                "role_in_joke": "铺垫",
                "visual": "两个人在咖啡馆正式相亲落座。",
                "dialogue": "你有房吗？",
                "caption": "气氛突然认真起来。",
                "image_prompt": "请绘制一张 1080x1440 的竖版单格漫画，表现咖啡馆里紧张的相亲开场。",
            },
            {
                "panel_number": 2,
                "role_in_joke": "推进",
                "visual": "程序员自信前倾，毫不迟疑地点头。",
                "dialogue": "有啊。",
                "caption": "预期被迅速抬高。",
                "image_prompt": "请绘制一张 1080x1440 的竖版单格漫画，表现程序员自信回应的推进镜头。",
            },
            {
                "panel_number": 3,
                "role_in_joke": "误导",
                "visual": "相亲对象露出惊喜表情，误会继续扩大。",
                "dialogue": "而且还不止一套。",
                "caption": "误会一路冲高。",
                "image_prompt": "请绘制一张 1080x1440 的竖版单格漫画，表现对方惊喜误解的误导镜头。",
            },
            {
                "panel_number": 4,
                "role_in_joke": "包袱",
                "visual": "程序员指向电脑上的 GitHub 仓库列表，对方瞬间愣住。",
                "dialogue": "我说的是 GitHub 上的仓库。",
                "caption": "包袱落地。",
                "image_prompt": "请绘制一张 1080x1440 的竖版单格漫画，表现 GitHub 真相揭晓的包袱镜头。",
            },
        ],
        "page_prompt": "请绘制一整页 2x2 四格漫画，用黑白喜剧漫画风格完整呈现这四个笑点节奏。",
    }

    monkeypatch.setattr(
        "backend.app.build_prompt_pack",
        lambda joke, confirmed_characters=None: fake_pack,
    )

    client = TestClient(app)
    response = client.post(
        "/api/joke-to-comic",
        json={"joke": "程序员去相亲，对方问他有没有房，他说 GitHub 上有好几套。"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["title"] == fake_pack["title"]
    assert body["source_joke"] == fake_pack["source_joke"]
    assert body["format"]["panel_count"] == 4
    assert body["format"]["image_width"] == 1080
    assert body["format"]["image_height"] == 1440
    assert body["format"]["page_layout"] == "2x2"
    assert len(body["panels"]) == 4
    assert all(panel["image_prompt"] for panel in body["panels"])
    assert all("1080x1440" in panel["image_prompt"] for panel in body["panels"])
    assert body["page_prompt"]


def test_joke_to_comic_accepts_confirmed_characters(monkeypatch):
    captured: dict[str, object] = {}

    def fake_build_prompt_pack(joke: str, confirmed_characters=None):
        captured["joke"] = joke
        captured["confirmed_characters"] = confirmed_characters
        return {
            "title": "系列试运行",
            "source_joke": joke,
            "format": {
                "panel_count": 4,
                "image_width": 1080,
                "image_height": 1440,
                "page_layout": "2x2",
            },
            "story_summary": "先确认主角，再生成本篇提示词包。",
            "humor_explanation": "笑点来自角色关系与误会推进。",
            "negative_prompt": "模糊，低清晰度，坏手，水印，标志",
            "generation_notes": [
                "保留 1080x1440 单格输出。",
                "保留 2x2 整页排版。",
            ],
            "panels": [
                {
                    "panel_number": 1,
                    "role_in_joke": "铺垫",
                    "visual": "产品经理和程序员在工位前对峙。",
                    "dialogue": "这个需求今天能改好吗？",
                    "caption": "",
                    "image_prompt": "请绘制一张 1080x1440 的漫画单格，角色已固定。",
                },
                {
                    "panel_number": 2,
                    "role_in_joke": "推进",
                    "visual": "程序员开始解释技术债。",
                    "dialogue": "理论上可以，现实上不行。",
                    "caption": "",
                    "image_prompt": "请绘制一张 1080x1440 的漫画单格，角色已固定。",
                },
                {
                    "panel_number": 3,
                    "role_in_joke": "误导",
                    "visual": "产品经理越听越觉得马上就能上线。",
                    "dialogue": "那就是快好了。",
                    "caption": "",
                    "image_prompt": "请绘制一张 1080x1440 的漫画单格，角色已固定。",
                },
                {
                    "panel_number": 4,
                    "role_in_joke": "包袱",
                    "visual": "程序员打开几十个待办卡片。",
                    "dialogue": "我是说理论上这周能开会。",
                    "caption": "",
                    "image_prompt": "请绘制一张 1080x1440 的漫画单格，角色已固定。",
                },
            ],
            "page_prompt": "请绘制一整页 2x2 四格漫画，角色已固定。",
        }

    monkeypatch.setattr("backend.app.build_prompt_pack", fake_build_prompt_pack)

    client = TestClient(app)
    confirmed_characters = [
        {
            "character_name": "美女产品经理",
            "series_role": "核心主角",
            "core_identity": "强势、节奏快、总在推动版本上线的产品经理",
            "visual_profile": "穿利落西装，长发，拿着需求文档",
            "personality_profile": "反应快，压迫感强，目标导向",
            "speech_style": "短句直给，常用反问",
            "relationship_to_others": "长期追着程序员改需求",
            "signature_elements": ["需求文档", "高跟鞋"],
            "character_prompt": "固定主角：美女产品经理，利落西装，强势表达。",
            "confidence_reason": "她承担了长期冲突与笑点推进。",
        },
        {
            "character_name": "屌丝程序员",
            "series_role": "核心主角",
            "core_identity": "总被需求追着跑、靠吐槽化解压力的程序员",
            "visual_profile": "格子衬衫，黑眼圈，抱着笔记本电脑",
            "personality_profile": "被动防守，自嘲，技术脑",
            "speech_style": "先解释再吐槽",
            "relationship_to_others": "长期被产品经理催更",
            "signature_elements": ["笔记本电脑", "工牌"],
            "character_prompt": "固定主角：屌丝程序员，格子衬衫，疲惫但嘴硬。",
            "confidence_reason": "他承担了反差与包袱落点。",
        },
    ]
    response = client.post(
        "/api/joke-to-comic",
        json={
            "joke": "美女产品经理追着程序员改需求，程序员说这周只能先开会。",
            "confirmed_characters": confirmed_characters,
        },
    )

    assert response.status_code == 200
    assert captured["joke"] == "美女产品经理追着程序员改需求，程序员说这周只能先开会。"
    forwarded_characters = [item.model_dump() for item in captured["confirmed_characters"]]
    assert forwarded_characters == confirmed_characters


def test_build_prompt_pack_generates_required_prompt_fields(monkeypatch):
    plan = ComicPlan(
        title="程序员相亲",
        story_summary="把房产误会改写成四格递进式笑点。",
        humor_explanation="笑点来自把仓库误听成房产，再在最后一格翻转。",
        art_style="黑白喜剧漫画",
        panels=[
            ComicPlanPanel(
                panel_number=1,
                role_in_joke="铺垫",
                visual="相亲对象和程序员在咖啡馆正式落座。",
                dialogue="你有房吗？",
                caption="问题来得很直接。",
            ),
            ComicPlanPanel(
                panel_number=2,
                role_in_joke="推进",
                visual="程序员非常自信地点头。",
                dialogue="有啊。",
                caption="气氛一下认真起来。",
            ),
            ComicPlanPanel(
                panel_number=3,
                role_in_joke="误导",
                visual="相亲对象开始露出惊喜表情，程序员继续补充。",
                dialogue="而且还不止一套。",
                caption="误会被拉满。",
            ),
            ComicPlanPanel(
                panel_number=4,
                role_in_joke="包袱",
                visual="电脑屏幕亮出 GitHub 仓库列表，相亲对象当场愣住。",
                dialogue="我说的是 GitHub 上的仓库。",
                caption="真相揭晓。",
            ),
        ],
    )

    monkeypatch.setattr(
        "backend.agents.joke_to_comic.generate_comic_plan",
        lambda joke: (plan, False),
    )

    prompt_pack = build_prompt_pack("程序员去相亲，对方问他有没有房，他说 GitHub 上有好几套。")

    assert prompt_pack.format.panel_count == 4
    assert len(prompt_pack.panels) == 4
    assert all(panel.image_prompt for panel in prompt_pack.panels)
    assert all("1080x1440" in panel.image_prompt for panel in prompt_pack.panels)
    assert "2x2" in prompt_pack.page_prompt
    assert "请绘制" in prompt_pack.panels[0].image_prompt
    assert "请绘制" in prompt_pack.page_prompt
    assert prompt_pack.page_prompt


def test_build_prompt_pack_embeds_confirmed_characters(monkeypatch):
    plan = ComicPlan(
        title="需求追更",
        story_summary="产品经理和程序员围绕需求追更不断拉扯，最后把包袱落在‘先开会’。",
        humor_explanation="笑点来自强推进和被动防守之间的稳定反差。",
        art_style="黑白喜剧漫画",
        panels=[
            ComicPlanPanel(
                panel_number=1,
                role_in_joke="铺垫",
                visual="产品经理冲到程序员工位前，甩下一叠新需求。",
                dialogue="这个版本今天一定要上。",
                caption="熟悉的追更又开始了。",
            ),
            ComicPlanPanel(
                panel_number=2,
                role_in_joke="推进",
                visual="程序员看着屏幕上密密麻麻的待办，表情僵硬。",
                dialogue="我连昨天的坑都还没填完。",
                caption="压力逐格叠高。",
            ),
            ComicPlanPanel(
                panel_number=3,
                role_in_joke="误导",
                visual="产品经理眯起眼睛，以为程序员马上就要给出交付时间。",
                dialogue="那你给我一个准话。",
                caption="读者也以为答案要来了。",
            ),
            ComicPlanPanel(
                panel_number=4,
                role_in_joke="包袱",
                visual="程序员举起会议邀请页面，像交差一样展示出来。",
                dialogue="这周能先开会。",
                caption="真正能交付的只有会议。",
            ),
        ],
    )

    monkeypatch.setattr(
        "backend.agents.joke_to_comic.generate_comic_plan",
        lambda joke: (plan, False),
    )

    confirmed_characters = [
        {
            "character_name": "美女产品经理",
            "series_role": "核心主角",
            "core_identity": "强势、节奏快、总在推动版本上线的产品经理",
            "visual_profile": "穿利落西装，长发，拿着需求文档",
            "personality_profile": "反应快，压迫感强，目标导向",
            "speech_style": "短句直给，常用反问",
            "relationship_to_others": "长期追着程序员改需求",
            "signature_elements": ["需求文档", "高跟鞋"],
            "character_prompt": "固定主角：美女产品经理，利落西装，强势表达。",
            "confidence_reason": "她承担了长期冲突与笑点推进。",
        },
        {
            "character_name": "屌丝程序员",
            "series_role": "核心主角",
            "core_identity": "总被需求追着跑、靠吐槽化解压力的程序员",
            "visual_profile": "格子衬衫，黑眼圈，抱着笔记本电脑",
            "personality_profile": "被动防守，自嘲，技术脑",
            "speech_style": "先解释再吐槽",
            "relationship_to_others": "长期被产品经理催更",
            "signature_elements": ["笔记本电脑", "工牌"],
            "character_prompt": "固定主角：屌丝程序员，格子衬衫，疲惫但嘴硬。",
            "confidence_reason": "他承担了反差与包袱落点。",
        },
    ]

    prompt_pack = build_prompt_pack(
        "美女产品经理追着程序员改需求，程序员说这周只能先开会。",
        confirmed_characters=confirmed_characters,
    )

    assert prompt_pack.format.image_width == 1080
    assert prompt_pack.format.image_height == 1440
    assert prompt_pack.format.page_layout == "2x2"
    assert "美女产品经理" in prompt_pack.panels[0].image_prompt
    assert "屌丝程序员" in prompt_pack.page_prompt
    assert any("已确认系列主角" in note for note in prompt_pack.generation_notes)
