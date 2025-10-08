# 业务场景实现示例

## 🎯 场景概述

本文档提供许可证创建API在不同业务场景下的完整实现示例，帮助前端开发者快速理解和集成各种实际业务需求。

## 📋 场景目录

1. [个人用户试用](#1-个人用户试用)
2. [小团队标准许可证](#2-小团队标准许可证)
3. [企业批量许可证](#3-企业批量许可证)
4. [教育机构许可证](#4-教育机构许可证)
5. [SaaS服务商场景](#5-saas服务商场景)
6. [临时项目许可证](#6-临时项目许可证)
7. [升级续费场景](#7-升级续费场景)
8. [紧急替换许可证](#8-紧急替换许可证)

## 1. 个人用户试用

### 场景描述
个人开发者申请30天试用版本，限制1台设备激活。

### 业务需求
- 试用期30天
- 单设备激活
- 快速开通
- 邮箱验证

### 实现代码

#### 前端表单
```jsx
const TrialLicenseForm = () => {
  const [formData, setFormData] = useState({
    customerName: '',
    customerEmail: '',
    company: ''
  });

  const createTrialLicense = async () => {
    const requestData = {
      plan: 1, // 试用版方案ID
      customer_info: {
        name: formData.customerName,
        email: formData.customerEmail,
        company: formData.company || '个人开发者'
      },
      max_activations: 1,
      validity_days: 30,
      notes: '个人用户试用版 - 30天试用期'
    };

    try {
      const response = await fetch('/api/v1/licenses/admin/licenses/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(requestData)
      });

      const license = await response.json();
      
      // 发送试用许可证邮件
      await sendTrialEmail(license);
      
      return license;
    } catch (error) {
      console.error('试用许可证创建失败:', error);
      throw error;
    }
  };

  return (
    <form>
      <input
        placeholder="您的姓名"
        value={formData.customerName}
        onChange={(e) => setFormData({...formData, customerName: e.target.value})}
        required
      />
      <input
        type="email"
        placeholder="邮箱地址"
        value={formData.customerEmail}
        onChange={(e) => setFormData({...formData, customerEmail: e.target.value})}
        required
      />
      <input
        placeholder="公司名称（可选）"
        value={formData.company}
        onChange={(e) => setFormData({...formData, company: e.target.value})}
      />
      <button onClick={createTrialLicense}>申请30天免费试用</button>
    </form>
  );
};
```

#### 发送邮件通知
```javascript
const sendTrialEmail = async (license) => {
  const emailData = {
    to: license.customer_email,
    subject: '您的试用许可证已准备就绪',
    template: 'trial_license',
    data: {
      customerName: license.customer_name,
      licenseKey: license.license_key,
      expiryDate: license.expires_at,
      downloadUrl: '/download/client',
      supportEmail: 'support@company.com'
    }
  };

  await fetch('/api/email/send/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(emailData)
  });
};
```

### 预期结果
```javascript
{
  "id": 101,
  "license_key": "TRIAL-12345-67890-ABCDE-FGHIJ",
  "customer_name": "张三",
  "customer_email": "zhangsan@gmail.com",
  "max_activations": 1,
  "current_activations": 0,
  "expires_at": "2024-10-27T10:30:00Z",
  "days_until_expiry": 30,
  "status": "active",
  "notes": "个人用户试用版 - 30天试用期"
}
```

## 2. 小团队标准许可证

### 场景描述
5-10人的小型开发团队购买年度许可证，需要支持多设备协作。

### 业务需求
- 年度有效期
- 5-10台设备
- 团队协作功能
- 技术支持

### 实现代码

#### 团队许可证创建
```javascript
const createTeamLicense = async (teamInfo, planId) => {
  const requestData = {
    plan: planId, // 团队版方案ID (通常是2或3)
    customer_info: {
      name: teamInfo.teamName,
      email: teamInfo.adminEmail,
      company: teamInfo.companyName,
      phone: teamInfo.phone,
      contact_person: teamInfo.teamLead
    },
    max_activations: teamInfo.teamSize,
    validity_days: 365,
    notes: `团队许可证 - ${teamInfo.teamSize}人团队 - 年度订阅`
  };

  try {
    const response = await fetch('/api/v1/licenses/admin/licenses/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      throw new Error(`创建失败: ${response.statusText}`);
    }

    const license = await response.json();
    
    // 创建团队成员记录
    await createTeamMembers(license.id, teamInfo.members);
    
    // 发送团队通知邮件
    await sendTeamNotification(license, teamInfo);
    
    return license;
  } catch (error) {
    console.error('团队许可证创建失败:', error);
    throw error;
  }
};
```

#### 团队成员管理
```javascript
const createTeamMembers = async (licenseId, members) => {
  const memberPromises = members.map(member => 
    fetch('/api/v1/licenses/team-members/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        license: licenseId,
        member_email: member.email,
        member_name: member.name,
        role: member.role || 'developer'
      })
    })
  );

  await Promise.all(memberPromises);
};

// 使用示例
const teamInfo = {
  teamName: '前端开发团队',
  companyName: '某某科技有限公司',
  adminEmail: 'team-lead@company.com',
  phone: '010-12345678',
  teamLead: '张经理',
  teamSize: 8,
  members: [
    { name: '开发者A', email: 'devA@company.com', role: 'senior' },
    { name: '开发者B', email: 'devB@company.com', role: 'junior' },
    { name: '设计师C', email: 'designC@company.com', role: 'designer' }
    // ... 更多成员
  ]
};

const teamLicense = await createTeamLicense(teamInfo, 2);
```

### 预期结果
```javascript
{
  "id": 102,
  "license_key": "TEAM8-ABCDE-FGHIJ-KLMNO-PQRST",
  "customer_name": "前端开发团队",
  "max_activations": 8,
  "validity_days": 365,
  "notes": "团队许可证 - 8人团队 - 年度订阅"
}
```

## 3. 企业批量许可证

### 场景描述
大型企业购买100-1000个许可证，需要统一管理和分配。

### 业务需求
- 大量设备支持
- 长期有效期
- 企业级功能
- 专属技术支持

### 实现代码

#### 企业许可证创建
```javascript
const createEnterpriseLicense = async (enterpriseInfo) => {
  const requestData = {
    plan: 4, // 企业版方案ID
    customer_info: {
      name: enterpriseInfo.companyName,
      email: enterpriseInfo.adminEmail,
      company: enterpriseInfo.companyName,
      phone: enterpriseInfo.phone,
      address: enterpriseInfo.address,
      contact_person: enterpriseInfo.contactPerson,
      department: enterpriseInfo.department
    },
    max_activations: enterpriseInfo.licenseCount,
    validity_days: enterpriseInfo.contractPeriod * 365, // 合同年数转天数
    notes: [
      `企业许可证 - ${enterpriseInfo.companyName}`,
      `合同编号: ${enterpriseInfo.contractNo}`,
      `许可数量: ${enterpriseInfo.licenseCount}`,
      `合同期限: ${enterpriseInfo.contractPeriod}年`,
      `销售代表: ${enterpriseInfo.salesRep}`
    ].join(' | ')
  };

  try {
    const response = await fetch('/api/v1/licenses/admin/licenses/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify(requestData)
    });

    const license = await response.json();
    
    // 创建企业管理记录
    await createEnterpriseManagement(license, enterpriseInfo);
    
    // 设置自动续费
    await setupAutoRenewal(license.id, enterpriseInfo.autoRenewal);
    
    return license;
  } catch (error) {
    console.error('企业许可证创建失败:', error);
    throw error;
  }
};

// 使用示例
const enterpriseInfo = {
  companyName: '大型科技集团有限公司',
  adminEmail: 'it-admin@bigcorp.com',
  phone: '010-88888888',
  address: '北京市朝阳区CBD核心区',
  contactPerson: 'IT总监-李先生',
  department: '信息技术部',
  licenseCount: 500,
  contractPeriod: 3, // 3年合同
  contractNo: 'ENT-2024-001',
  salesRep: '销售经理-王女士',
  autoRenewal: true
};

const enterpriseLicense = await createEnterpriseLicense(enterpriseInfo);
```

#### 企业管理功能
```javascript
const createEnterpriseManagement = async (license, enterpriseInfo) => {
  // 创建管理员账户
  await fetch('/api/v1/enterprise/admins/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      license_id: license.id,
      admin_email: enterpriseInfo.adminEmail,
      admin_name: enterpriseInfo.contactPerson,
      permissions: ['manage_licenses', 'view_reports', 'manage_users']
    })
  });

  // 设置使用配额
  await fetch('/api/v1/enterprise/quotas/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      license_id: license.id,
      max_concurrent_users: enterpriseInfo.licenseCount,
      max_projects: enterpriseInfo.licenseCount * 2,
      storage_quota_gb: enterpriseInfo.licenseCount * 10
    })
  });
};
```

### 预期结果
```javascript
{
  "id": 103,
  "license_key": "ENT50-ABCDE-FGHIJ-KLMNO-PQRST",
  "customer_name": "大型科技集团有限公司",
  "max_activations": 500,
  "validity_days": 1095,
  "notes": "企业许可证 - 大型科技集团有限公司 | 合同编号: ENT-2024-001 | 许可数量: 500 | 合同期限: 3年"
}
```

## 4. 教育机构许可证

### 场景描述
大学或培训机构为教学和实验申请教育版许可证，享受教育折扣。

### 业务需求
- 教育优惠价格
- 学年有效期
- 大量并发用户
- 教学功能支持

### 实现代码

#### 教育许可证创建
```javascript
const createEducationLicense = async (educationInfo) => {
  const requestData = {
    plan: 5, // 教育版方案ID
    customer_info: {
      name: `${educationInfo.institutionName} - ${educationInfo.department}`,
      email: educationInfo.adminEmail,
      company: educationInfo.institutionName,
      phone: educationInfo.phone,
      address: educationInfo.address,
      contact_person: educationInfo.contactPerson,
      department: educationInfo.department
    },
    max_activations: educationInfo.studentCount + educationInfo.teacherCount,
    validity_days: educationInfo.academicYear ? 365 : 180, // 学年或学期
    notes: [
      `教育机构许可证 - ${educationInfo.institutionName}`,
      `学生数量: ${educationInfo.studentCount}`,
      `教师数量: ${educationInfo.teacherCount}`,
      `学期类型: ${educationInfo.academicYear ? '学年' : '学期'}`,
      `课程名称: ${educationInfo.courseName}`
    ].join(' | ')
  };

  try {
    const response = await fetch('/api/v1/licenses/admin/licenses/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify(requestData)
    });

    const license = await response.json();
    
    // 设置教育功能
    await setupEducationFeatures(license.id, educationInfo);
    
    // 创建班级管理
    await createClassManagement(license.id, educationInfo.classes);
    
    return license;
  } catch (error) {
    console.error('教育许可证创建失败:', error);
    throw error;
  }
};

// 使用示例
const educationInfo = {
  institutionName: '北京理工大学',
  department: '计算机科学与技术学院',
  adminEmail: 'cs-admin@bit.edu.cn',
  phone: '010-68912345',
  address: '北京市海淀区中关村南大街5号',
  contactPerson: '计算机系-张教授',
  studentCount: 200,
  teacherCount: 10,
  academicYear: true, // 学年许可证
  courseName: '软件工程实践',
  classes: [
    { name: '软工1班', students: 50 },
    { name: '软工2班', students: 50 },
    { name: '软工3班', students: 50 },
    { name: '软工4班', students: 50 }
  ]
};

const educationLicense = await createEducationLicense(educationInfo);
```

#### 教育功能设置
```javascript
const setupEducationFeatures = async (licenseId, educationInfo) => {
  await fetch('/api/v1/education/features/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      license_id: licenseId,
      features: {
        classroom_mode: true,
        assignment_management: true,
        progress_tracking: true,
        collaborative_editing: true,
        teacher_dashboard: true,
        student_submission: true
      },
      restrictions: {
        commercial_use: false,
        external_sharing: false,
        advanced_analytics: false
      }
    })
  });
};
```

### 预期结果
```javascript
{
  "id": 104,
  "license_key": "EDU21-ABCDE-FGHIJ-KLMNO-PQRST",
  "customer_name": "北京理工大学 - 计算机科学与技术学院",
  "max_activations": 210,
  "validity_days": 365,
  "notes": "教育机构许可证 - 北京理工大学 | 学生数量: 200 | 教师数量: 10"
}
```

## 5. SaaS服务商场景

### 场景描述
SaaS平台需要为其客户动态创建和管理许可证。

### 业务需求
- API自动化创建
- 动态扩容
- 计费集成
- 多租户隔离

### 实现代码

#### SaaS许可证管理
```javascript
class SaaSLicenseManager {
  constructor(apiToken) {
    this.apiToken = apiToken;
    this.baseUrl = '/api/v1/licenses/admin/licenses/';
  }

  // 为SaaS客户创建许可证
  async createCustomerLicense(saasCustomer, planType) {
    const planMapping = {
      'starter': 2,
      'professional': 3,
      'enterprise': 4
    };

    const requestData = {
      plan: planMapping[planType],
      customer_info: {
        name: `SaaS客户 - ${saasCustomer.companyName}`,
        email: saasCustomer.adminEmail,
        company: saasCustomer.companyName,
        phone: saasCustomer.phone,
        contact_person: saasCustomer.contactPerson
      },
      max_activations: saasCustomer.userLimit,
      validity_days: saasCustomer.billingCycle === 'monthly' ? 30 : 365,
      notes: [
        `SaaS客户许可证 - ${saasCustomer.companyName}`,
        `客户ID: ${saasCustomer.id}`,
        `订阅类型: ${planType}`,
        `计费周期: ${saasCustomer.billingCycle}`,
        `创建来源: SaaS平台`
      ].join(' | ')
    };

    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiToken}`
      },
      body: JSON.stringify(requestData)
    });

    const license = await response.json();
    
    // 关联到SaaS客户记录
    await this.linkToSaaSCustomer(license.id, saasCustomer.id);
    
    // 设置使用监控
    await this.setupUsageMonitoring(license.id, saasCustomer);
    
    return license;
  }

  // 根据使用量自动扩容
  async autoScale(licenseId, currentUsage) {
    const license = await this.getLicense(licenseId);
    const utilizationRate = currentUsage / license.max_activations;
    
    if (utilizationRate > 0.8) { // 使用率超过80%
      const newLimit = Math.ceil(license.max_activations * 1.5);
      await this.updateLicenseLimit(licenseId, newLimit);
      
      // 通知计费系统
      await this.notifyBillingSystem(licenseId, newLimit);
    }
  }

  async getLicense(licenseId) {
    const response = await fetch(`${this.baseUrl}${licenseId}/`, {
      headers: { 'Authorization': `Bearer ${this.apiToken}` }
    });
    return await response.json();
  }

  async updateLicenseLimit(licenseId, newLimit) {
    await fetch(`${this.baseUrl}${licenseId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiToken}`
      },
      body: JSON.stringify({ max_activations: newLimit })
    });
  }
}

// 使用示例
const licenseManager = new SaaSLicenseManager('your-api-token');

const saasCustomer = {
  id: 'CUST-12345',
  companyName: 'Client Corporation',
  adminEmail: 'admin@client.com',
  phone: '010-12345678',
  contactPerson: 'IT Manager',
  userLimit: 25,
  billingCycle: 'monthly'
};

const license = await licenseManager.createCustomerLicense(saasCustomer, 'professional');
```

### 预期结果
```javascript
{
  "id": 105,
  "license_key": "SAAS2-ABCDE-FGHIJ-KLMNO-PQRST",
  "customer_name": "SaaS客户 - Client Corporation",
  "max_activations": 25,
  "validity_days": 30,
  "notes": "SaaS客户许可证 - Client Corporation | 客户ID: CUST-12345 | 订阅类型: professional"
}
```

## 6. 临时项目许可证

### 场景描述
为临时项目或短期合作创建有限期的许可证。

### 业务需求
- 短期有效期
- 项目绑定
- 有限功能
- 到期自动停用

### 实现代码

```javascript
const createProjectLicense = async (projectInfo) => {
  const requestData = {
    plan: 2, // 项目版方案
    customer_info: {
      name: `项目：${projectInfo.projectName}`,
      email: projectInfo.projectManagerEmail,
      company: projectInfo.clientCompany,
      phone: projectInfo.phone,
      contact_person: projectInfo.projectManager
    },
    max_activations: projectInfo.teamSize,
    validity_days: projectInfo.projectDuration,
    notes: [
      `临时项目许可证`,
      `项目名称: ${projectInfo.projectName}`,
      `项目周期: ${projectInfo.projectDuration}天`,
      `项目开始: ${projectInfo.startDate}`,
      `项目结束: ${projectInfo.endDate}`
    ].join(' | ')
  };

  const response = await fetch('/api/v1/licenses/admin/licenses/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(requestData)
  });

  const license = await response.json();
  
  // 设置项目到期提醒
  await scheduleExpiryReminder(license.id, projectInfo.endDate);
  
  return license;
};

// 使用示例
const projectInfo = {
  projectName: '电商平台开发项目',
  clientCompany: '零售集团有限公司',
  projectManagerEmail: 'pm@retailgroup.com',
  phone: '010-87654321',
  projectManager: '项目经理-陈女士',
  teamSize: 12,
  projectDuration: 90, // 90天项目
  startDate: '2024-09-27',
  endDate: '2024-12-26'
};

const projectLicense = await createProjectLicense(projectInfo);
```

## 7. 升级续费场景

### 场景描述
客户从基础版升级到高级版，或者续费现有许可证。

### 业务需求
- 无缝升级
- 数据迁移
- 价格差异处理
- 历史记录保留

### 实现代码

```javascript
const upgradeCustomerLicense = async (currentLicenseId, newPlanId) => {
  // 获取当前许可证信息
  const currentLicense = await fetch(`/api/v1/licenses/admin/licenses/${currentLicenseId}/`);
  const current = await currentLicense.json();
  
  // 创建升级后的新许可证
  const upgradeData = {
    plan: newPlanId,
    customer_info: {
      name: current.customer_name,
      email: current.customer_email,
      // 复用现有客户信息
    },
    max_activations: Math.max(current.max_activations, 50), // 升级后设备数
    validity_days: 365, // 新的年度许可证
    notes: [
      `升级许可证 - 从许可证#${currentLicenseId}升级`,
      `原方案: ${current.plan_name}`,
      `升级日期: ${new Date().toISOString().split('T')[0]}`,
      `升级原因: 客户业务扩展需要更多功能`
    ].join(' | ')
  };

  const response = await fetch('/api/v1/licenses/admin/licenses/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(upgradeData)
  });

  const newLicense = await response.json();
  
  // 迁移现有设备绑定
  await migrateMachineBindings(currentLicenseId, newLicense.id);
  
  // 停用旧许可证
  await deactivateOldLicense(currentLicenseId, '升级到新许可证');
  
  return newLicense;
};
```

## 8. 紧急替换许可证

### 场景描述
客户的许可证出现问题或丢失，需要紧急创建替换许可证。

### 业务需求
- 快速处理
- 保留原有配置
- 应急授权
- 问题追踪

### 实现代码

```javascript
const createEmergencyReplacement = async (originalLicenseId, reason) => {
  const originalLicense = await fetch(`/api/v1/licenses/admin/licenses/${originalLicenseId}/`);
  const original = await originalLicense.json();
  
  const emergencyData = {
    plan: original.plan,
    customer_info: {
      name: original.customer_name,
      email: original.customer_email,
      // 复用原有信息
    },
    max_activations: original.max_activations,
    validity_days: Math.max(30, original.days_until_expiry), // 至少30天
    notes: [
      `紧急替换许可证`,
      `原许可证ID: ${originalLicenseId}`,
      `替换原因: ${reason}`,
      `创建时间: ${new Date().toISOString()}`,
      `操作员: 客服部门`
    ].join(' | ')
  };

  const response = await fetch('/api/v1/licenses/admin/licenses/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    },
    body: JSON.stringify(emergencyData)
  });

  const emergencyLicense = await response.json();
  
  // 记录紧急操作日志
  await logEmergencyOperation(originalLicenseId, emergencyLicense.id, reason);
  
  // 发送紧急通知
  await sendEmergencyNotification(emergencyLicense, reason);
  
  return emergencyLicense;
};

// 使用示例
const emergencyLicense = await createEmergencyReplacement(
  123, 
  '客户报告许可证服务器故障无法验证'
);
```

## 🔧 通用工具函数

### 1. 批量创建许可证
```javascript
const batchCreateLicenses = async (licenseDataList) => {
  const results = [];
  const errors = [];
  
  for (const [index, licenseData] of licenseDataList.entries()) {
    try {
      const response = await fetch('/api/v1/licenses/admin/licenses/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(licenseData)
      });
      
      if (response.ok) {
        const license = await response.json();
        results.push({ index, license });
      } else {
        const error = await response.json();
        errors.push({ index, error });
      }
    } catch (error) {
      errors.push({ index, error: error.message });
    }
    
    // 添加延迟避免API限流
    if (index < licenseDataList.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  return { results, errors };
};
```

### 2. 许可证使用监控
```javascript
const monitorLicenseUsage = async (licenseId) => {
  const response = await fetch(`/api/v1/licenses/admin/licenses/${licenseId}/usage-stats/`);
  const stats = await response.json();
  
  const alerts = [];
  
  // 检查激活数量接近限制
  if (stats.current_activations / stats.max_activations > 0.8) {
    alerts.push({
      type: 'activation_limit',
      message: '激活数量接近限制',
      current: stats.current_activations,
      limit: stats.max_activations
    });
  }
  
  // 检查即将过期
  if (stats.days_until_expiry < 30) {
    alerts.push({
      type: 'expiry_warning',
      message: '许可证即将过期',
      daysLeft: stats.days_until_expiry
    });
  }
  
  return { stats, alerts };
};
```

## 📝 最佳实践总结

1. **字段验证**: 始终在前端验证必需字段
2. **错误处理**: 实现完整的错误处理和用户提示
3. **状态管理**: 正确管理加载状态和禁用状态
4. **数据备份**: 保存重要的许可证信息
5. **用户体验**: 提供清晰的进度指示和成功反馈
6. **安全考虑**: 妥善处理敏感信息和API令牌
7. **性能优化**: 合理使用缓存和批量操作

---

**下一步**: 查看 [错误处理指南](error_handling.md) 学习如何处理各种异常情况。
