# 管理员用户管理模块 - 流程图

本文档提供管理员用户管理模块的主要流程图，帮助前端开发人员理解模块的结构和各页面间的关系。

## 模块结构图

下图展示了管理员用户管理模块的主要组成部分及其关系：

```mermaid
graph TD
    A[管理员用户模块] --> B[管理员列表]
    A --> C[创建管理员]
    A --> D[管理员详情]
    A --> E[编辑管理员]
    A --> F[当前管理员信息]
    A --> G[超级管理员创建]
    
    B --> B1[搜索和筛选]
    B --> B2[表格显示]
    B --> B3[分页控制]
    B --> B4[批量操作]
    
    C --> C1[基本信息表单]
    C --> C2[账号设置表单]
    C --> C3[表单验证]
    
    D --> D1[基本信息显示]
    D --> D2[权限管理]
    D --> D3[账号安全]
    
    E --> E1[编辑基本信息]
    E --> E2[修改权限]
    E --> E3[状态管理]
    
    F --> F1[个人资料显示]
    F --> F2[修改个人信息]
    F --> F3[修改密码]
    F --> F4[上传头像]
    
    G --> G1[超级管理员表单]
    G --> G2[权限警告]
```

## 用户操作流程图

下图展示了管理员用户常见操作的流程：

```mermaid
graph TD
    Start[开始] --> Login[用户登录]
    Login --> CheckRole{检查用户角色}
    
    CheckRole -->|超级管理员| SuperAdmin[显示完整管理功能]
    CheckRole -->|租户管理员| TenantAdmin[显示有限管理功能]
    
    SuperAdmin --> SA1[查看所有管理员]
    SuperAdmin --> SA2[创建任何租户管理员]
    SuperAdmin --> SA3[创建超级管理员]
    SuperAdmin --> SA4[授予/撤销超级管理员权限]
    
    TenantAdmin --> TA1[查看本租户管理员]
    TenantAdmin --> TA2[创建本租户管理员]
    
    SA1 --> ViewDetail[查看管理员详情]
    TA1 --> ViewDetail
    
    SA2 --> CreateFlow[创建管理员流程]
    TA2 --> CreateFlow
    SA3 --> CreateSuperAdmin[创建超级管理员流程]
    
    ViewDetail --> EditOption{编辑选项}
    EditOption -->|编辑信息| EditInfo[编辑基本信息]
    EditOption -->|修改权限| EditRole[修改角色权限]
    EditOption -->|删除账号| DeleteAccount[删除账号]
    
    CreateFlow --> FillBasicInfo[填写基本信息]
    FillBasicInfo --> FillAccountSettings[填写账号设置]
    FillAccountSettings --> ValidateForm{表单验证}
    ValidateForm -->|验证通过| SaveUser[保存用户]
    ValidateForm -->|验证失败| ShowErrors[显示错误信息]
    ShowErrors --> FillBasicInfo
    
    CreateSuperAdmin --> FillSuperAdminInfo[填写超级管理员信息]
    FillSuperAdminInfo --> ConfirmPrivilege[确认特殊权限]
    ConfirmPrivilege --> ValidateSuperAdmin{表单验证}
    ValidateSuperAdmin -->|验证通过| SaveSuperAdmin[保存超级管理员]
    ValidateSuperAdmin -->|验证失败| ShowSuperAdminErrors[显示错误信息]
    ShowSuperAdminErrors --> FillSuperAdminInfo
    
    SaveUser --> Success[操作成功]
    SaveSuperAdmin --> Success
    EditInfo --> Success
    EditRole --> Success
    DeleteAccount --> Success
    
    Success --> End[结束]
```

## 密码修改流程图

下图展示了管理员修改密码的流程：

```mermaid
graph TD
    Start[开始] --> OpenDialog[打开密码修改对话框]
    OpenDialog --> InputCurrentPwd[输入当前密码]
    InputCurrentPwd --> InputNewPwd[输入新密码]
    InputNewPwd --> InputConfirmPwd[输入确认密码]
    
    InputConfirmPwd --> Validate{验证密码}
    
    Validate -->|验证失败| ShowError[显示错误信息]
    ShowError --> InputCurrentPwd
    
    Validate -->|验证通过| SubmitChange[提交修改]
    
    SubmitChange --> VerifyServer{服务器验证}
    
    VerifyServer -->|验证失败| ShowServerError[显示服务器错误]
    ShowServerError --> InputCurrentPwd
    
    VerifyServer -->|验证通过| ChangeSuccess[密码修改成功]
    
    ChangeSuccess --> CloseDialog[关闭对话框]
    CloseDialog --> End[结束]
```

## 头像上传流程图

下图展示了管理员上传头像的流程：

```mermaid
graph TD
    Start[开始] --> OpenDialog[打开头像上传对话框]
    OpenDialog --> SelectImage[选择图片]
    SelectImage --> PreviewCrop[预览和裁剪]
    
    PreviewCrop --> AdjustImage[调整图片]
    AdjustImage --> Confirm{确认上传}
    
    Confirm -->|取消| CloseDialog[关闭对话框]
    CloseDialog --> End[结束]
    
    Confirm -->|确认| UploadImage[上传图片]
    
    UploadImage --> UploadStatus{上传状态}
    UploadStatus -->|失败| ShowError[显示错误]
    ShowError --> SelectImage
    
    UploadStatus -->|成功| UpdateAvatar[更新头像显示]
    UpdateAvatar --> CloseSuccessDialog[关闭对话框]
    CloseSuccessDialog --> End
```

这些流程图提供了管理员用户模块主要功能的操作流程，帮助前端开发人员理解用户交互和页面跳转逻辑。 