```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Database
    
    %% 文章管理流程
    rect rgb(240, 240, 240)
    Note over User,Database: 文章管理流程
    User->>Frontend: 创建/编辑文章
    Frontend->>API: 提交文章数据
    API->>Database: 保存文章
    Database-->>API: 返回保存结果
    API-->>Frontend: 返回操作状态
    Frontend-->>User: 显示成功/失败提示
    end
    
    %% 评论流程
    rect rgb(230, 240, 255)
    Note over User,Database: 评论流程
    User->>Frontend: 提交评论
    Frontend->>API: 发送评论数据
    API->>Database: 保存评论(待审核)
    Database-->>API: 返回保存结果
    API-->>Frontend: 返回评论状态
    Frontend-->>User: 显示"评论已提交"
    
    alt 需要审核
        Note over User,Database: 审核流程
        API->>Database: 查询待审核评论
        Database-->>API: 返回评论列表
        API-->>Frontend: 显示待审核列表
        User->>Frontend: 批准评论
        Frontend->>API: 发送批准请求
        API->>Database: 更新评论状态
    end
    end
    
    %% 分类标签管理
    rect rgb(245, 240, 225)
    Note over User,Database: 分类标签管理
    User->>Frontend: 创建分类/标签
    Frontend->>API: 提交分类/标签数据
    API->>Database: 保存分类/标签
    Database-->>API: 返回保存结果
    API-->>Frontend: 返回操作状态
    Frontend-->>User: 更新分类/标签树
    
    User->>Frontend: 拖拽调整顺序
    Frontend->>API: 发送排序数据
    API->>Database: 更新排序信息
    end
    
    %% 统计分析流程
    rect rgb(230, 245, 230)
    Note over User,Database: 统计分析流程
    User->>Frontend: 查看统计仪表板
    Frontend->>API: 请求统计数据
    API->>Database: 查询统计信息
    Database-->>API: 返回统计数据
    API-->>Frontend: 返回格式化数据
    Frontend-->>User: 显示图表和指标
    
    User->>Frontend: 互动(点赞/收藏)
    Frontend->>Frontend: 即时更新UI状态
    Frontend->>API: 发送互动请求
    API->>Database: 记录互动行为
    Database-->>API: 更新统计计数
    end 