"""
Idempotent data migration syncing VisCase image-grounded case copy,
ArticleMeta SEO records, VisShow bilingual category metadata,
and VisCase application description, then clearing API cache.
"""

from django.db import IntegrityError, migrations
from django.utils import timezone


VISCASE_APP_COPY = {
    "id": 18,
    "code": "viscase",
    "tenant_id": 100,
    "name": "VisCase",
    "description": (
        "专注城市形象标识、地理标志农品版画包装、餐饮国潮角色 IP 与非遗老字号复兴的实体视觉案例展厅。"
    ),
}

VISCASE_CATEGORY_TRANSLATIONS = {
    "zh-hans": {
        "name": "VisShow",
        "description": (
            "VisCase 视觉设计与品牌实案精选，涵盖城市形象标识、地理标志农品包装、餐饮角色 IP 与非遗老字号共 12 组完整案例。"
        ),
        "seo_title": "VisShow 视觉品牌全案档案 - VisCase Studio",
        "seo_description": (
            "VisCase 视觉设计与品牌实案精选，涵盖城市形象标识、地理标志农品包装、餐饮角色 IP 与非遗老字号共 12 组完整案例。"
        ),
    },
    "en": {
        "name": "VisShow",
        "description": (
            "Curated VisCase brand identity, agro-geographic engraving, culinary character IP, and cultural heritage archive."
        ),
        "seo_title": "VisShow Case Archive - VisCase Studio",
        "seo_description": (
            "Curated VisCase brand identity, agro-geographic engraving, culinary character IP, and cultural heritage archive."
        ),
    },
}

VISCASE_DB_CASES = [
    {
        "id": 102,
        "slug": "viscase-case-p-1",
        "code": "P-1",
        "title": "丹江口 · 南水北调源头城市形象标识",
        "excerpt": "以“山水太极”圆徽融合金色古城楼剪影与湛蓝清泉水滴，配以点划含水的手书体“丹江口”，凝练南水北调源头的生态气韵与人文底色。",
        "seo_keywords": "丹江口, 城市形象标识, 南水北调, 山水太极, 书法字标",
        "content": """## 城市气质与双意象太极构图

作为南水北调中线工程核心水源区，丹江口兼顾千年底蕴与一泓清水。主标志放弃传统城市徽标的刻板对称，构建起「上城下水、金蓝交抱」的太极圆境：

- **上半圆暖阳古建**：明亮朝阳金映照重檐古城楼剪影与远山天际线，锚定地域历史人文；
- **下半圆清冽水滴**：饱满晶莹的蔚蓝大水滴带着高光反弧顺势包托，象征充沛且源源不断的生命碧水。

## 手书字标与细节呼应

中文主标“丹江口”以雄浑而不失灵动的手书行草挥就，特意将**“江”字首点化作一滴悬垂晶蓝水珠**，令文字笔意直接呼应上方图形主标；右下英文 `Dan Jiang Kou` 与底部宽字距细宋体「南水北调源头城市」稳健承托，从城市门户雕塑、水系文旅导览牌到地方礼盒包装均可从容延展。

## 核心视觉与印制参数

- **推荐主辅色板**：`#0B56A8` 丹江深蓝 / `#1498D5` 清泉天青 / `#F2CD2A` 朝阳暖金
- **核心交付项**：城市主视觉徽标 · 手书书法字标 · 中英双语组合规范 · 文旅导视延展""",
    },
    {
        "id": 103,
        "slug": "viscase-case-p-2",
        "code": "P-2",
        "title": "大庄缘® · 康凯黄金羊拐品牌标识与视觉系统",
        "excerpt": "炽热朱红双旋祥云符号兼具草原羊角张力与宴席喜庆感，左嵌“康凯”篆刻红印，围绕「家有贵客」确立礼宴美食记忆点。",
        "seo_keywords": "大庄缘, 康凯, 黄金羊拐, 餐饮品牌标识, 篆刻红印",
        "content": """## 从地方特色菜升级为宴席礼赠符号

黄金羊拐自带肉香与团圆宴请属性，但传统牛羊肉品牌容易陷入写实照片堆砌的同质化。设计提炼一气呵成的**朱红双旋曲线**：三条弧线回旋聚散，远观如草原牧羊昂扬的双角，近赏似宴席升腾的热气与东方吉祥祥云。

## 字印协同与待客主张

- **厚重字标稳住商业分量**：焦墨玄黑敦厚黑体“大庄缘®”醒目稳重，搭配左下细线“康凯”椭圆朱文篆章，赋予现代食品品牌源自老字号手艺与品控的权威背书；
- **场景化定位标语**：底部清俊宋体「家有贵客 · 就吃大庄缘黄金羊拐」与主体形成粗细反差，精准占领家庭聚餐、年节伴手礼盒及实体门头识别心智。

## 核心视觉与印制参数

- **推荐主辅色板**：`#FC4C27` 炽焰朱红 / `#222021` 焦墨玄黑 / `#D92727` 印泥丹红
- **核心交付项**：品牌超级符号 · 字标与朱红篆印 · 礼盒主视觉标语 · 门店门头系统""",
    },
    {
        "id": 104,
        "slug": "viscase-case-p-3",
        "code": "P-3",
        "title": "三十度硒农业 · 天然富硒农场圆形徽标设计",
        "excerpt": "深林墨绿构筑的等高线梯田、古亭与硕果枝叶浓缩于正圆之中，搭配现代圆角细线字标，呈现纯净可信赖的自然农场气质。",
        "seo_keywords": "三十度硒农业, 生态农业标识, 富硒农场, 等高线徽标",
        "content": """## 把整座富硒山谷装进一枚自然圆印

针对都市家庭对原生态与安全食材的高标准审视，三十度硒农业需要彻底告别传统农批市场的杂乱印象。圆徽内构筑了一座秩序井然的微型农庄：

- **韵律梯田底座**：下半圆采用同心环抱与平行走向的深林绿等高线条，勾勒起伏丘陵、灌渠与水田涟漪；
- **亭台枝果点睛**：上半圆林枝交错、飞檐古亭掩映山巅，其中点缀两枚高明度赤橙果实与数片翠绿新叶，沉稳中透出生机。

## 极简等线字体与包材泛用性

品牌中文名“三十度硒农业”选用笔画均匀圆润的现代无衬线线条体，底部搭配宽字距细宋体「我家的天然农场 三十度硒」。整套单线条系统可无损微缩应用于牛皮纸箱丝网直印、茶罐锡封钢印与农庄导视铁艺牌。

## 核心视觉与印制参数

- **推荐主辅色板**：`#1B462D` 森林深绿 / `#F5A600` 暖阳金果 / `#E64A19` 生态赤果
- **核心交付项**：农场主视觉徽章 · 定制圆角字标 · 农产品贴标规范 · 农庄导视图标""",
    },
    {
        "id": 105,
        "slug": "viscase-case-p-4",
        "code": "P-4",
        "title": "关口葡萄 · 沐栖庄园地理标志版画与礼盒视觉",
        "excerpt": "东方线描版画架构起祥云、石砌关楼“関陽景”与两侧低垂硕果葡萄藤，协同“三十度硒农业×沐栖庄园”母子标识铸就庄园级地理名片。",
        "seo_keywords": "关口葡萄, 沐栖庄园, 関陽景, 地理标志包装, 版画插画",
        "content": """## 以地方关城与精细版画确立风土名片

地方名果从批发散装跃升为精品伴手礼盒，核心在于“可感知的风土建筑故事与印刷精细感”。设计团队结合当地文化地标实景，创作了整幅中轴对称单色钢笔版画：

- **关楼风物叙事**：正中石阶向上延伸，石砌城墙与门额“関陽景”清晰可辨，远山绵延，左右两侧垂落粒粒饱满晶莹、卷须缠绕的成串葡萄；
- **严谨母子品牌层级**：拱顶祥云正中稳妥嵌入“三十度硒农业”圆形生态母标与“沐栖庄园®”副牌字标，下承大字号定制几何体“关口葡萄”与宽间距拼音 `GUAN KOU PU TAO`。

## 兼顾箱装直印与礼盒烫金的工艺精度

整幅图形依托统一的墨绿专色单线与排线阴影塑造立体感，既能在生鲜物流瓦楞箱低成本单色柔印保持锐利不糊版，也可在高端节日礼盒面上执行专色烫墨绿金与击凸触感。

## 核心视觉与印制参数

- **推荐主辅色板**：`#1B462D` 藤蔓森绿 / `#3B6B4F` 苔青石阶 / `#FAFBF9` 宣纸素白
- **核心交付项**：礼盒核心版画插画 · 主副品牌层级规范 · 地理标志定制字标 · 手提礼箱视觉""",
    },
    {
        "id": 106,
        "slug": "viscase-case-p-5",
        "code": "P-5",
        "title": "楼下生鲜 · 佰佳社区生鲜零售视觉与图形字标",
        "excerpt": "鲜明柠檬黄配翠绿的高能量撞色圆标，将活鱼、橙片果籽与下行阶梯巧融入字形之中，配合「远亲不如近邻」直击社区生活圈。",
        "seo_keywords": "楼下生鲜, 佰佳, 社区零售视觉, 图形字标, 门店招牌",
        "content": """## 三秒看懂“就在楼下、生鲜齐全、邻里相伴”

社区生鲜便利店面对的是高频次、快速决策的日常街坊客群。标志摒弃冷淡克制的精品超市范式，打造出一枚自带果蔬生命力的**高亮柠黄大圆徽**——右上翘起两片鲜嫩黄叶，宛如一枚硕大新鲜的柑橘，在小区出入口或夜晚灯光下极为抢眼。

## 藏在笔画里的食材趣味暗喻

- **“楼”字化鱼**：左偏旁化作一条立身游弋的小鲜鱼；
- **“下”字筑阶**：右点延展成两级向下的小台阶，巧妙扣合“下楼买菜”；
- **“鲜”字生果**：将左侧“鱼”部改为带两片嫩叶、内含多粒果籽的圆形切片鲜果；
- **街坊信任锁扣**：左侧叠印深绿圆形「佰佳」品牌母印，中栏直白呼出「远亲不如近邻」，亲和力与识别度兼具。

## 核心视觉与印制参数

- **推荐主辅色板**：`#F7ED08` 鲜柠明黄 / `#037A67` 生鲜翠绿 / `#FFFFFF` 洁净纯白
- **核心交付项**：门店高对比门头标识 · 趣味图形汉字设计 · 环保购物袋与围裙 · 冷鲜价签系统""",
    },
    {
        "id": 107,
        "slug": "viscase-case-p-6",
        "code": "P-6",
        "title": "川疆娃 CHUAN JIANG WA · 水墨熊猫大厨 IP 形象",
        "excerpt": "戴厨师高帽、弯眼甜笑且顽皮舔舌的水墨大熊猫 IP 头像，携手厚重苍劲毛笔字“川疆娃”，引爆浓郁巴蜀烟火食欲感。",
        "seo_keywords": "川疆娃, 熊猫大厨, 餐饮 IP, 书法字标, 川菜视觉",
        "content": """## 一只馋嘴舔唇的熊猫大厨，胜过十句美食口号

川味餐饮视觉最忌晦涩抽象。品牌提取最具川渝亲和力的熊猫原型，用粗细自然、富有笔刷肌理的墨线描摹出一只头顶高厨帽、弯眉笑眼、**伸出正红小舌头轻舔嘴唇**的大厨头像——“刚尝一口就被惊艳”的表情瞬间唤醒路人与外卖食客的食欲。

## 泼墨书法与极简网格字体的撞击

- **厚重手书中文**：“川疆娃”采粗壮沉稳的泼墨楷行书写，笔画收尾留有手写钝锋与墨韵；
- **现代英文基底**：正下方紧跟宽字重几何黑体 `CHUAN JIANG WA`，让市井烟火气与当代连锁餐企的专业感达成平衡；
- **低成本双色延展**：全标几乎只由浓墨炭黑与一抹点绛红组成，在外带纸袋、牛皮纸碗、员工围裙与门头灯箱上均极耐看且印制成本可控。

## 核心视觉与印制参数

- **推荐主辅色板**：`#1F1A17` 浓墨炭黑 / `#D6381A` 川辣点绛红 / `#FFFFFF` 宣纸留白
- **核心交付项**：熊猫大厨核心 IP · 定制手书字标 · 外卖包材与餐具贴标 · 门店导视贴纸""",
    },
    {
        "id": 108,
        "slug": "viscase-case-p-7",
        "code": "P-7",
        "title": "本宫的酒 · 宫廷窗棂字标与 Q 版贵妃角色 IP",
        "excerpt": "朱红复古宫廷窗棂框住飞檐微翘的篆韵字标，右下站立凤冠绣金红袍的俏皮 Q 版贵妃人物，塑造极具戏剧反差感的新潮酒饮名片。",
        "seo_keywords": "本宫的酒, 新国潮酒饮, 宫廷 IP, 窗棂字标, 瓶贴设计",
        "content": """## 当庄重宫墙遇见一点傲娇微醺感

面向都市年轻客群的新国潮果酒与低度特调酒，需要彻底摆脱传统高度白酒的刻板厚重。「本宫的酒」将皇家御酿意象转化为年轻社交场景的戏剧化趣味名片：

- **建筑飞檐田字窗格**：外框四边端点微微上翘如宫殿翘檐，“本、宫、的、酒”四字融入窗棂篆意，竖横圆转对称，天然构成酒瓶正标的高识别框徽；
- **破框站立的俏皮小贵妃**：人物置于右下角跨出边框，细绘金凤花冠、红玛瑙流苏耳坠与暗金祥云滚边绯红宽袍，眼波微斜、神态略带小娇嗔与傲娇萌态，一举拉近与女生小聚小酌的情感共鸣。

## 核心视觉与印制参数

- **推荐主辅色板**：`#EA4B54` 宫墙朱绯红 / `#B91C1B` 华服绛紫红 / `#DFBB43` 鎏金翠钿
- **核心交付项**：贵妃人物角色 IP · 定制宫窗字标 · 瓶身烫金主标与外盒 · 盲盒周边衍生物料""",
    },
    {
        "id": 109,
        "slug": "viscase-case-p-8",
        "code": "P-8",
        "title": "牛元源 · 「只做牛的味道」品牌 IP 与描边字标",
        "excerpt": "亮黄圆日中的眨眼小红牛搭配牛角笔锋的描边黑字“牛元源”，底层 Slogan 独将“牛”字点红，强势占位牛肉细分赛道。",
        "seo_keywords": "牛元源, 牛肉餐饮, 卡通牛 IP, 描边字标, 门店招牌",
        "content": """## 赢下街头行人的“两秒钟就餐决策”

鲜切牛肉火锅与牛肉粉面竞争极其激烈，门店招牌必须兼顾欢乐烟火感与品类直觉。「牛元源」避开写实牛头雕塑的肃杀感，在暖阳黄大圆底托中塑造出一只**左眼调皮眨眼、咧嘴笑迎八方客、手持圆头金勺**的赤红萌牛。

## 字画同源的牛角结构与红字主张

- **牛角字标造型**：“牛”与“源”字外展横勾自然延展出双只锐利而翘皮的黄金弧角曲线，中间“元”字巧嵌圆满太极环框，整体再以粗厚咖啡玄墨描边聚合，醒目立体；
- **品类核心字凸显**：底层标语「只做牛的味道」中唯独将**“牛”字放红放大**，配合俏皮笔画断点，让食客隔街即懂门店主打核心。

## 核心视觉与印制参数

- **推荐主辅色板**：`#F7F321` 暖阳亮黄 / `#DE5841` 红牛赭绯 / `#281D18` 厚重铁墨
- **核心交付项**：元气小牛 IP 形象 · 牛角描边定制字标 · 品类核心 Slogan · 连锁菜单与灯箱规范""",
    },
    {
        "id": 110,
        "slug": "viscase-case-p-9",
        "code": "P-9",
        "title": "猎渔村 · 重庆老坛酸菜鱼国潮人物与木版字标",
        "excerpt": "头戴竹编斗笠、怀抱“李”记老坛与鲜活江鱼的渔夫插画，搭配红棕木刻竖排“猎渔村”，定格地道重庆酸菜鱼的江湖烟火。",
        "seo_keywords": "猎渔村, 重庆老坛酸菜鱼, 国潮渔夫插画, 木版字标",
        "content": """## 把“鲜活江鱼 + 李氏老坛”端到消费者眼前

地道重庆老坛酸菜鱼的核心竞争力在于食材鲜度与秘制老坛功底。设计团队拒绝空洞口号，创作了一幅信息满载、神采飞扬的国潮川江渔夫插画：

- **角色道具皆为卖点**：渔夫头戴精细编织的竹斗笠、身背竹制抄网与写有「猎」字的鹅黄襟袍，一臂怀抱贴着红菱形楷体**“李”记密封老坛**，一臂牢牢抱住泛着青蓝鳞光的**鲜活江鱼**，身后翻腾的炽红川辣浪花带出浓烈江湖气；
- **巴渝木版竖排三栏字标**：最左大号「猎渔村」以饱含刻刀劲道与高光镂空的红棕雕版字体竖排，中栏以红色泡菜老坛剪影分隔「经典 · 传承」，右栏清晰落款「重庆老坛酸菜鱼」，极其契合原木牌匾与复古餐饮空间壁画。

## 核心视觉与印制参数

- **推荐主辅色板**：`#B92D21` 老坛红椒褐 / `#EFB55B` 竹编斗笠黄 / `#6F88BC` 活鱼青鳞蓝
- **核心交付项**：国潮渔夫主插画 · 木版竖排字标 · 实木牌匾与主题墙绘 · 外带餐盒围裙视觉""",
    },
    {
        "id": 111,
        "slug": "viscase-case-p-10",
        "code": "P-10",
        "title": "怡脉 YI MAI · 「偲享生活·品味怡脉」极简字体识别",
        "excerpt": "澄澈湖水青单线构成呼吸感极简字体，“心”旁渐染水叶、右上轻栖青鸟剪影，传递轻盈松弛的东方现代健康美学。",
        "seo_keywords": "怡脉, YI MAI, 极简字标, 健康生活方式, 松石青",
        "content": """## 以呼吸感视觉完成货架与心智的“瞬间降噪”

在堆满繁复功效标签的大健康与生活方式市场，克制通透反而极具辨识力。「怡脉」放弃沉重图形底块，采用高挑修长、线条如一缕清风的极简现代汉字构建核心记忆：

- **“心生水叶、脉栖青鸟”的微隐喻**：“怡”字左部竖心旁以柔和的蓝白渐层化作两片舒展水叶，“脉”字右上角悄然停驻一只正待振翅的渐变青鸟，暗喻心身畅达、自然吐纳的生命韵律；
- **流动双波标语结构**：中英文 `YI MAI` 两侧延展出修长柔美的水波单线，正下方细线镂空字体「偲享生活 · 品味怡脉」如微光透影，纯净而高雅。

## 核心视觉与印制参数

- **推荐主辅色板**：`#0CB2C9` 松石湖青 / `#8ADBE7` 清泉浅青渐变 / `#FFFFFF` 纯净留白
- **核心交付项**：极简主视觉字标 · 渐层微符号规范 · 磨砂瓶器丝印与烫银应用 · 导视字体系统""",
    },
    {
        "id": 112,
        "slug": "viscase-case-p-11",
        "code": "P-11",
        "title": "狮筹之路 SHICHOU ZHILU · 醒狮造像与狂草飞白字标",
        "excerpt": "重彩手绘南派醒狮正面威武狮首，碰撞力透纸背的干湿飞白狂草“狮筹之路”，将非遗醒狮精神注入当代潮流视觉。",
        "seo_keywords": "狮筹之路, 醒狮, 非遗国潮, 狂草飞白, 文化 IP",
        "content": """## 工笔重彩狮首与狂草大飞白的张力碰撞

国潮文创若只有常规工笔配电脑字体，往往流于装饰。本案刻意将两种截然不同的笔墨语言并置在同一视觉中轴：

- **正面威仪南派醒狮**：高饱和重彩搭配有力浓墨勾勒出黄金独角额镜、松石青眉脊、雪白卷须、绛红颧颊与金黄胡须流苏，构图正面稳重、细节经得起放大端详；
- **破空而出的一记干湿飞白**：主字标“狮筹之路”纵横跌宕——“狮”字立柱竖笔挺拔下拉如旗杆，“路”字底横顺势爆裂横扫出苍劲飞白长尾，仿佛醒狮凌空甩尾带风；下方字隙巧嵌紧凑几何英文 `SHICHOU ZHILU`，令千年非遗一眼步入当代潮流语境。

## 核心视觉与印制参数

- **推荐主辅色板**：`#1B1918` 泼墨焦黑 / `#CE261F` 醒狮正红 / `#3B9C9C` 点翠额青
- **核心交付项**：醒狮高精度手绘插画 · 狂草飞白大字标 · 文创服饰印花稿 · 联名礼盒主画面""",
    },
    {
        "id": 113,
        "slug": "viscase-case-p-12",
        "code": "P-12",
        "title": "广东揭阳 1992 · 老师傅手艺肖像与匠心印章徽标",
        "excerpt": "暖金海棠窗框与辐射晨光烘托微笑捧碗的老师傅雕版肖像，结合「广东·揭阳·始于1992年」及四枚「匠·心·傳·承」古印，沉淀老字号温度。",
        "seo_keywords": "广东揭阳, 1992, 老字号, 手工面食, 匠心传承, 创始人肖像",
        "content": """## 三十年老字号最好的商标，就是掌柜捧碗的那双手

面对海量快消与半成品食饮竞争，老字号品牌最不可复制的护城河在于真实的时间、手艺与掌柜温度。设计直接以**真实创始人肖像版画**作为最高信任凭证：

- **晨光海棠框中的端碗微笑**：采用温润熟褐细密木刻线条描摹出老师傅慈祥诚恳、双手稳托一碗满盛细面与祥云瓷碗的定格瞬间；身后是传统多重海棠菱花窗棂与放射状晨光虚线，映照清晨生灶揉面的烟火气息；
- **纪年背书与古印钤记**：头像下方明确标注「广东 · 揭阳 · 始于 1992 年」地理与创立纪年，底座一字排开「匠」「心」「傳」「承」四枚仿木刻印章，在麦浪暖金底衬上散发深厚的非遗手造公信力。

## 核心视觉与印制参数

- **推荐主辅色板**：`#EBBF26` 麦浪暖金 / `#856228` 熟褐木刻线 / `#F7F3EB` 手工米白
- **核心交付项**：创始人雕版肖像徽标 · 匠心传承四枚印章体系 · 面食礼盒腰封 · 门店灯光门头规范""",
    },
]


def clear_api_cache_safely():
    try:
        from django.core.cache import cache

        cache.clear()
        return True
    except Exception:
        return False


def apply_viscase_copy(apps_registry, db_alias="default", clear_cache=True):
    Application = apps_registry.get_model("applications", "Application")
    Category = apps_registry.get_model("cms", "Category")
    CategoryTranslation = apps_registry.get_model("cms", "CategoryTranslation")
    Article = apps_registry.get_model("cms", "Article")
    ArticleMeta = apps_registry.get_model("cms", "ArticleMeta")

    now = timezone.now()
    summary = {
        "application_updated": False,
        "category_updated": False,
        "articles_updated": 0,
        "cache_cleared": False,
    }

    # 1. Update Application (VisCase)
    app = (
        Application.objects.using(db_alias)
        .filter(
            code__iexact=VISCASE_APP_COPY["code"],
            tenant_id=VISCASE_APP_COPY["tenant_id"],
            is_deleted=False,
        )
        .first()
        or Application.objects.using(db_alias)
        .filter(
            id=VISCASE_APP_COPY["id"],
            tenant_id=VISCASE_APP_COPY["tenant_id"],
            is_deleted=False,
        )
        .first()
    )
    if app is not None:
        app.name = VISCASE_APP_COPY["name"]
        app.description = VISCASE_APP_COPY["description"]
        app.updated_at = now
        app.save(using=db_alias, update_fields=["name", "description", "updated_at"])
        summary["application_updated"] = True

    # 2. Update Category (VisShow) bilingual translations directly via historical table model
    cat = (
        Category.objects.using(db_alias)
        .filter(slug="visshow", tenant_id=100, is_deleted=False)
        .first()
        or Category.objects.using(db_alias)
        .filter(id=127, tenant_id=100, is_deleted=False)
        .first()
    )
    if cat is not None:
        for lang_code, fields in VISCASE_CATEGORY_TRANSLATIONS.items():
            defaults = {
                "name": fields["name"],
                "description": fields["description"],
                "seo_title": fields["seo_title"],
                "seo_description": fields["seo_description"],
            }
            try:
                CategoryTranslation.objects.using(db_alias).update_or_create(
                    master_id=cat.id,
                    language_code=lang_code,
                    defaults=defaults,
                )
            except IntegrityError:
                CategoryTranslation.objects.using(db_alias).filter(
                    master_id=cat.id,
                    language_code=lang_code,
                ).update(**defaults)
        cat.updated_at = now
        cat.save(using=db_alias, update_fields=["updated_at"])
        summary["category_updated"] = True

    # 3. Update VisCase Articles & ArticleMeta
    for item in VISCASE_DB_CASES:
        article = (
            Article.objects.using(db_alias)
            .filter(slug=item["slug"], is_deleted=False)
            .first()
            or Article.objects.using(db_alias)
            .filter(id=item["id"], tenant_id=100, is_deleted=False)
            .first()
        )
        if article is None:
            continue

        article.title = item["title"]
        article.excerpt = item["excerpt"]
        article.content = item["content"]
        article.content_type = "markdown"
        article.updated_at = now
        article.save(
            using=db_alias,
            update_fields=["title", "excerpt", "content", "content_type", "updated_at"],
        )

        meta_defaults = {
            "tenant_id": article.tenant_id,
            "is_deleted": False,
            "seo_title": f"{item['title']} - VisCase",
            "seo_description": item["excerpt"],
            "seo_keywords": item["seo_keywords"],
            "og_title": item["title"],
            "og_description": item["excerpt"],
            "og_image": article.cover_image,
        }
        try:
            ArticleMeta.objects.using(db_alias).update_or_create(
                article_id=article.id,
                defaults=meta_defaults,
            )
        except IntegrityError:
            ArticleMeta.objects.using(db_alias).filter(article_id=article.id).update(
                updated_at=now,
                **meta_defaults,
            )
        summary["articles_updated"] += 1

    if clear_cache:
        summary["cache_cleared"] = clear_api_cache_safely()

    return summary


def forwards(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    apply_viscase_copy(apps, db_alias=db_alias, clear_cache=True)


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0016_sync_article_intermediate_tenants"),
        ("applications", "0005_userapplication"),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
