# 客户端集成示例

## 📖 概述

本文档提供macOS应用程序集成许可证系统的详细示例代码，包括Swift/Objective-C实现的硬件指纹获取、许可证激活、验证和心跳检测功能。

## 🍎 macOS Swift 集成示例

### 1. 硬件信息收集

```swift
import Foundation
import IOKit
import CommonCrypto

class HardwareInfoCollector {
    
    // 获取系统信息
    func getSystemInfo() -> [String: Any] {
        let processInfo = ProcessInfo.processInfo
        
        return [
            "os_version": processInfo.operatingSystemVersionString,
            "hostname": processInfo.hostName,
            "architecture": getArchitecture(),
            "kernel_version": getKernelVersion()
        ]
    }
    
    // 获取CPU信息
    func getCPUInfo() -> [String: Any] {
        var size = 0
        sysctlbyname("machdep.cpu.brand_string", nil, &size, nil, 0)
        var cpuBrand = [CChar](repeating: 0, count: size)
        sysctlbyname("machdep.cpu.brand_string", &cpuBrand, &size, nil, 0)
        
        return [
            "brand": String(cString: cpuBrand),
            "core_count": ProcessInfo.processInfo.processorCount,
            "frequency": getCPUFrequency()
        ]
    }
    
    // 获取内存信息
    func getMemoryInfo() -> [String: Any] {
        let physicalMemory = ProcessInfo.processInfo.physicalMemory
        
        return [
            "total_bytes": physicalMemory,
            "total_gb": Double(physicalMemory) / 1024.0 / 1024.0 / 1024.0
        ]
    }
    
    // 获取硬件UUID
    func getHardwareUUID() -> String? {
        let platformExpert = IOServiceGetMatchingService(kIOMasterPortDefault,
                                                       IOServiceMatching("IOPlatformExpertDevice"))
        
        guard platformExpert > 0 else { return nil }
        
        guard let serialNumberAsCFString = IORegistryEntryCreateCFProperty(
            platformExpert,
            kIOPlatformUUIDKey as CFString,
            kCFAllocatorDefault, 0) else {
                IOObjectRelease(platformExpert)
                return nil
        }
        
        IOObjectRelease(platformExpert)
        
        return serialNumberAsCFString.takeUnretainedValue() as? String
    }
    
    // 获取网络接口信息
    func getNetworkInterfaces() -> [[String: Any]] {
        // 实现网络接口信息获取
        // 这里简化处理
        return []
    }
    
    // 获取完整硬件信息
    func getCompleteHardwareInfo() -> [String: Any] {
        return [
            "system_info": getSystemInfo(),
            "cpu_info": getCPUInfo(),
            "memory_info": getMemoryInfo(),
            "hardware_uuid": getHardwareUUID() ?? "unknown",
            "network_interfaces": getNetworkInterfaces(),
            "collected_at": ISO8601DateFormatter().string(from: Date())
        ]
    }
    
    // 辅助方法
    private func getArchitecture() -> String {
        var systemInfo = utsname()
        uname(&systemInfo)
        return withUnsafePointer(to: &systemInfo.machine) {
            $0.withMemoryRebound(to: CChar.self, capacity: 1) {
                String(validatingUTF8: $0) ?? "unknown"
            }
        }
    }
    
    private func getKernelVersion() -> String {
        var systemInfo = utsname()
        uname(&systemInfo)
        return withUnsafePointer(to: &systemInfo.release) {
            $0.withMemoryRebound(to: CChar.self, capacity: 1) {
                String(validatingUTF8: $0) ?? "unknown"
            }
        }
    }
    
    private func getCPUFrequency() -> Int {
        var frequency: Int = 0
        var size = MemoryLayout<Int>.size
        sysctlbyname("hw.cpufrequency", &frequency, &size, nil, 0)
        return frequency
    }
}
```

### 2. 许可证管理器

```swift
import Foundation

class LicenseManager {
    private let baseURL = "https://your-api-domain.com/api/v1/licenses"
    private let hardwareCollector = HardwareInfoCollector()
    
    // 激活许可证
    func activateLicense(licenseKey: String, completion: @escaping (Result<ActivationResult, Error>) -> Void) {
        let hardwareInfo = hardwareCollector.getCompleteHardwareInfo()
        
        let requestBody: [String: Any] = [
            "license_key": licenseKey,
            "hardware_info": hardwareInfo,
            "client_info": [
                "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] ?? "1.0.0",
                "platform": "macOS",
                "client_type": "native_app"
            ]
        ]
        
        makeAPIRequest(
            endpoint: "/activate/",
            method: "POST",
            body: requestBody
        ) { result in
            switch result {
            case .success(let data):
                if let activationResult = self.parseActivationResponse(data) {
                    completion(.success(activationResult))
                } else {
                    completion(.failure(LicenseError.invalidResponse))
                }
            case .failure(let error):
                completion(.failure(error))
            }
        }
    }
    
    // 验证激活状态
    func verifyActivation(activationCode: String, completion: @escaping (Result<VerificationResult, Error>) -> Void) {
        let machineFingerprint = generateMachineFingerprint()
        
        let requestBody: [String: Any] = [
            "activation_code": activationCode,
            "machine_fingerprint": machineFingerprint
        ]
        
        makeAPIRequest(
            endpoint: "/verify/",
            method: "POST",
            body: requestBody
        ) { result in
            switch result {
            case .success(let data):
                if let verificationResult = self.parseVerificationResponse(data) {
                    completion(.success(verificationResult))
                } else {
                    completion(.failure(LicenseError.invalidResponse))
                }
            case .failure(let error):
                completion(.failure(error))
            }
        }
    }
    
    // 发送心跳
    func sendHeartbeat(activationCode: String, eventType: String, eventData: [String: Any]? = nil, completion: @escaping (Result<HeartbeatResult, Error>) -> Void) {
        let requestBody: [String: Any] = [
            "activation_code": activationCode,
            "event_type": eventType,
            "event_data": eventData ?? [:],
            "software_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] ?? "1.0.0",
            "session_id": UUID().uuidString,
            "system_status": [
                "cpu_usage": getCurrentCPUUsage(),
                "memory_usage": getCurrentMemoryUsage()
            ]
        ]
        
        makeAPIRequest(
            endpoint: "/heartbeat/",
            method: "POST",
            body: requestBody
        ) { result in
            switch result {
            case .success(let data):
                if let heartbeatResult = self.parseHeartbeatResponse(data) {
                    completion(.success(heartbeatResult))
                } else {
                    completion(.failure(LicenseError.invalidResponse))
                }
            case .failure(let error):
                completion(.failure(error))
            }
        }
    }
    
    // 生成机器指纹
    private func generateMachineFingerprint() -> String {
        let hardwareInfo = hardwareCollector.getCompleteHardwareInfo()
        
        // 提取关键信息用于指纹生成
        let fingerprintData: [String: Any] = [
            "hardware_uuid": hardwareInfo["hardware_uuid"] ?? "",
            "cpu_brand": (hardwareInfo["cpu_info"] as? [String: Any])?["brand"] ?? "",
            "total_memory": (hardwareInfo["memory_info"] as? [String: Any])?["total_bytes"] ?? 0,
            "hostname": (hardwareInfo["system_info"] as? [String: Any])?["hostname"] ?? ""
        ]
        
        // 生成JSON字符串并计算SHA-256哈希
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: fingerprintData)
            return sha256(data: jsonData)
        } catch {
            return "error-generating-fingerprint"
        }
    }
    
    // 通用API请求方法
    private func makeAPIRequest(endpoint: String, method: String, body: [String: Any]? = nil, completion: @escaping (Result<Data, Error>) -> Void) {
        guard let url = URL(string: baseURL + endpoint) else {
            completion(.failure(LicenseError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("MyMacApp/1.0.0", forHTTPHeaderField: "User-Agent")
        
        if let body = body {
            do {
                request.httpBody = try JSONSerialization.data(withJSONObject: body)
            } catch {
                completion(.failure(error))
                return
            }
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(LicenseError.noData))
                    return
                }
                
                completion(.success(data))
            }
        }.resume()
    }
    
    // 解析响应的辅助方法
    private func parseActivationResponse(_ data: Data) -> ActivationResult? {
        do {
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            guard let success = json?["success"] as? Bool, success else {
                return nil
            }
            
            let responseData = json?["data"] as? [String: Any]
            return ActivationResult(
                activationCode: responseData?["activation_code"] as? String ?? "",
                machineId: responseData?["machine_id"] as? String ?? "",
                expiresAt: responseData?["expires_at"] as? String,
                features: responseData?["features"] as? [String: Any] ?? [:]
            )
        } catch {
            return nil
        }
    }
    
    private func parseVerificationResponse(_ data: Data) -> VerificationResult? {
        do {
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            guard let valid = json?["valid"] as? Bool else {
                return nil
            }
            
            return VerificationResult(
                valid: valid,
                licenseInfo: json?["license_info"] as? [String: Any],
                lastVerified: json?["last_verified"] as? String
            )
        } catch {
            return nil
        }
    }
    
    private func parseHeartbeatResponse(_ data: Data) -> HeartbeatResult? {
        do {
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            guard let success = json?["success"] as? Bool else {
                return nil
            }
            
            return HeartbeatResult(
                success: success,
                message: json?["message"] as? String,
                licenseStatus: json?["license_status"] as? [String: Any],
                warnings: json?["warnings"] as? [String]
            )
        } catch {
            return nil
        }
    }
    
    // 系统状态获取
    private func getCurrentCPUUsage() -> Double {
        // 实现CPU使用率获取
        return 0.0
    }
    
    private func getCurrentMemoryUsage() -> Double {
        // 实现内存使用率获取
        return 0.0
    }
    
    // SHA-256哈希计算
    private func sha256(data: Data) -> String {
        var digest = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes {
            _ = CC_SHA256($0.baseAddress, CC_LONG(data.count), &digest)
        }
        return digest.map { String(format: "%02hhx", $0) }.joined()
    }
}

// 数据结构定义
struct ActivationResult {
    let activationCode: String
    let machineId: String
    let expiresAt: String?
    let features: [String: Any]
}

struct VerificationResult {
    let valid: Bool
    let licenseInfo: [String: Any]?
    let lastVerified: String?
}

struct HeartbeatResult {
    let success: Bool
    let message: String?
    let licenseStatus: [String: Any]?
    let warnings: [String]?
}

// 错误定义
enum LicenseError: Error {
    case invalidURL
    case noData
    case invalidResponse
    case activationFailed(String)
    case verificationFailed(String)
}
```

### 3. 应用程序集成示例

```swift
import Cocoa

class AppDelegate: NSObject, NSApplicationDelegate {
    private let licenseManager = LicenseManager()
    private var activationCode: String?
    private var heartbeatTimer: Timer?
    
    func applicationDidFinishLaunching(_ aNotification: Notification) {
        // 检查许可证状态
        checkLicenseStatus()
    }
    
    func applicationWillTerminate(_ aNotification: Notification) {
        // 发送应用关闭事件
        if let activationCode = activationCode {
            licenseManager.sendHeartbeat(
                activationCode: activationCode,
                eventType: "shutdown"
            ) { _ in }
        }
        
        // 停止心跳定时器
        heartbeatTimer?.invalidate()
    }
    
    // 检查许可证状态
    private func checkLicenseStatus() {
        // 从Keychain或用户偏好设置中获取保存的激活码
        if let savedActivationCode = getSavedActivationCode() {
            verifyExistingLicense(activationCode: savedActivationCode)
        } else {
            // 显示许可证输入界面
            showLicenseInputDialog()
        }
    }
    
    // 验证现有许可证
    private func verifyExistingLicense(activationCode: String) {
        licenseManager.verifyActivation(activationCode: activationCode) { [weak self] result in
            switch result {
            case .success(let verificationResult):
                if verificationResult.valid {
                    self?.activationCode = activationCode
                    self?.startApplication()
                } else {
                    self?.showLicenseInputDialog()
                }
            case .failure(_):
                self?.showLicenseInputDialog()
            }
        }
    }
    
    // 显示许可证输入对话框
    private func showLicenseInputDialog() {
        let alert = NSAlert()
        alert.messageText = "许可证激活"
        alert.informativeText = "请输入您的许可证密钥："
        alert.addButton(withTitle: "激活")
        alert.addButton(withTitle: "退出")
        
        let textField = NSTextField(frame: NSRect(x: 0, y: 0, width: 300, height: 24))
        textField.placeholderString = "XXXXX-XXXXX-XXXXX-XXXXX"
        alert.accessoryView = textField
        
        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            let licenseKey = textField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
            if !licenseKey.isEmpty {
                activateLicense(licenseKey: licenseKey)
            } else {
                showLicenseInputDialog()
            }
        } else {
            NSApplication.shared.terminate(self)
        }
    }
    
    // 激活许可证
    private func activateLicense(licenseKey: String) {
        // 显示进度指示器
        let progressAlert = createProgressAlert(message: "正在激活许可证...")
        
        licenseManager.activateLicense(licenseKey: licenseKey) { [weak self] result in
            progressAlert.close()
            
            switch result {
            case .success(let activationResult):
                // 保存激活码
                self?.saveActivationCode(activationResult.activationCode)
                self?.activationCode = activationResult.activationCode
                
                // 显示成功消息
                self?.showSuccessAlert(message: "许可证激活成功！")
                self?.startApplication()
                
            case .failure(let error):
                // 显示错误消息
                self?.showErrorAlert(error: error)
                self?.showLicenseInputDialog()
            }
        }
    }
    
    // 启动应用程序主要功能
    private func startApplication() {
        // 发送启动事件
        if let activationCode = activationCode {
            licenseManager.sendHeartbeat(
                activationCode: activationCode,
                eventType: "startup",
                eventData: [
                    "launch_time": Date().timeIntervalSince1970,
                    "launch_source": "user_click"
                ]
            ) { _ in }
        }
        
        // 启动定期心跳
        startHeartbeatTimer()
        
        // 这里启动您的主要应用程序逻辑
        print("应用程序已启动，许可证验证成功")
    }
    
    // 启动心跳定时器
    private func startHeartbeatTimer() {
        heartbeatTimer = Timer.scheduledTimer(withTimeInterval: 300.0, repeats: true) { [weak self] _ in
            guard let activationCode = self?.activationCode else { return }
            
            self?.licenseManager.sendHeartbeat(
                activationCode: activationCode,
                eventType: "heartbeat"
            ) { result in
                // 处理心跳响应
                switch result {
                case .success(let heartbeatResult):
                    if let warnings = heartbeatResult.warnings, !warnings.isEmpty {
                        // 处理警告（如许可证即将过期）
                        DispatchQueue.main.async {
                            self?.showWarningAlert(warnings: warnings)
                        }
                    }
                case .failure(_):
                    // 心跳失败，可能需要重新验证许可证
                    break
                }
            }
        }
    }
    
    // 辅助方法
    private func getSavedActivationCode() -> String? {
        return UserDefaults.standard.string(forKey: "ActivationCode")
    }
    
    private func saveActivationCode(_ code: String) {
        UserDefaults.standard.set(code, forKey: "ActivationCode")
    }
    
    private func createProgressAlert(message: String) -> NSAlert {
        let alert = NSAlert()
        alert.messageText = message
        alert.addButton(withTitle: "取消")
        // 在实际应用中，这里应该创建一个带进度指示器的自定义视图
        return alert
    }
    
    private func showSuccessAlert(message: String) {
        let alert = NSAlert()
        alert.alertStyle = .informational
        alert.messageText = "成功"
        alert.informativeText = message
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }
    
    private func showErrorAlert(error: Error) {
        let alert = NSAlert()
        alert.alertStyle = .critical
        alert.messageText = "激活失败"
        alert.informativeText = error.localizedDescription
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }
    
    private func showWarningAlert(warnings: [String]) {
        let alert = NSAlert()
        alert.alertStyle = .warning
        alert.messageText = "许可证警告"
        alert.informativeText = warnings.joined(separator: "\n")
        alert.addButton(withTitle: "确定")
        alert.runModal()
    }
}
```

## 🌐 HTTP客户端示例 (cURL)

### 1. 获取许可证信息

```bash
# 获取许可证基本信息
curl -X GET "https://your-api-domain.com/api/v1/licenses/info/ABCD1-EFGH2-IJKL3-MNOP4/" \
  -H "User-Agent: MyMacApp/1.0.0"
```

### 2. 激活许可证

```bash
# 激活许可证
curl -X POST "https://your-api-domain.com/api/v1/licenses/activate/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyMacApp/1.0.0" \
  -d '{
    "license_key": "ABCD1-EFGH2-IJKL3-MNOP4",
    "hardware_info": {
      "system_info": {
        "os_version": "macOS 13.0",
        "hostname": "MacBook-Pro.local",
        "architecture": "arm64",
        "kernel_version": "22.1.0"
      },
      "cpu_info": {
        "brand": "Apple M2",
        "core_count": 8,
        "frequency": 3200000000
      },
      "memory_info": {
        "total_bytes": 17179869184,
        "total_gb": 16.0
      },
      "hardware_uuid": "12345678-1234-5678-9ABC-123456789ABC",
      "network_interfaces": [],
      "collected_at": "2024-01-15T10:30:00Z"
    },
    "client_info": {
      "app_version": "1.0.0",
      "platform": "macOS",
      "client_type": "native_app"
    }
  }'
```

### 3. 验证激活状态

```bash
# 验证激活状态
curl -X POST "https://your-api-domain.com/api/v1/licenses/verify/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyMacApp/1.0.0" \
  -d '{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "machine_fingerprint": "sha256:a1b2c3d4e5f6..."
  }'
```

### 4. 发送心跳

```bash
# 发送心跳
curl -X POST "https://your-api-domain.com/api/v1/licenses/heartbeat/" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyMacApp/1.0.0" \
  -d '{
    "activation_code": "ACT-12345678-ABCD-EFGH",
    "event_type": "heartbeat",
    "event_data": {
      "feature_used": "export_data",
      "export_count": 5
    },
    "software_version": "1.0.0",
    "session_id": "session-12345",
    "system_status": {
      "cpu_usage": 45.2,
      "memory_usage": 62.8
    }
  }'
```

## 🛡️ 安全最佳实践

### 1. 密钥存储

```swift
import Security

class SecureStorage {
    
    // 安全存储激活码
    static func saveActivationCode(_ code: String) -> Bool {
        let data = code.data(using: .utf8)!
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "MyMacApp",
            kSecAttrAccount as String: "ActivationCode",
            kSecValueData as String: data
        ]
        
        SecItemDelete(query as CFDictionary)
        return SecItemAdd(query as CFDictionary, nil) == errSecSuccess
    }
    
    // 安全读取激活码
    static func getActivationCode() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "MyMacApp",
            kSecAttrAccount as String: "ActivationCode",
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var dataTypeRef: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &dataTypeRef)
        
        if status == errSecSuccess {
            if let data = dataTypeRef as? Data {
                return String(data: data, encoding: .utf8)
            }
        }
        
        return nil
    }
}
```

### 2. 网络安全

```swift
// SSL证书验证
extension LicenseManager: URLSessionDelegate {
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        
        // 实施证书固定
        guard let serverTrust = challenge.protectionSpace.serverTrust else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        
        // 验证证书链
        let policy = SecPolicyCreateSSL(true, "your-api-domain.com" as CFString)
        SecTrustSetPolicies(serverTrust, policy)
        
        var evaluation: SecTrustResultType = .invalid
        let status = SecTrustEvaluate(serverTrust, &evaluation)
        
        if status == errSecSuccess && (evaluation == .proceed || evaluation == .unspecified) {
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
        } else {
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
}
```

### 3. 防篡改检测

```swift
// 应用程序完整性检查
class IntegrityChecker {
    
    static func verifyApplicationIntegrity() -> Bool {
        guard let bundlePath = Bundle.main.bundlePath as NSString? else {
            return false
        }
        
        // 检查代码签名
        return verifyCodeSignature(bundlePath: bundlePath.standardizingPath)
    }
    
    private static func verifyCodeSignature(bundlePath: String) -> Bool {
        var staticCode: SecStaticCode?
        let status = SecStaticCodeCreateWithPath(URL(fileURLWithPath: bundlePath) as CFURL, [], &staticCode)
        
        guard status == errSecSuccess, let code = staticCode else {
            return false
        }
        
        return SecStaticCodeCheckValidity(code, [], nil) == errSecSuccess
    }
}
```

## 📱 使用示例

```swift
// 在应用启动时使用
class ViewController: NSViewController {
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // 检查应用完整性
        guard IntegrityChecker.verifyApplicationIntegrity() else {
            showIntegrityError()
            return
        }
        
        // 检查许可证
        checkLicense()
    }
    
    private func checkLicense() {
        if let activationCode = SecureStorage.getActivationCode() {
            // 验证现有许可证
            verifyLicense(activationCode: activationCode)
        } else {
            // 请求用户输入许可证
            requestLicenseInput()
        }
    }
    
    private func verifyLicense(activationCode: String) {
        // 实现许可证验证逻辑
    }
    
    private func requestLicenseInput() {
        // 实现许可证输入界面
    }
    
    private func showIntegrityError() {
        let alert = NSAlert()
        alert.messageText = "应用程序完整性验证失败"
        alert.informativeText = "应用程序可能已被篡改，请重新下载。"
        alert.runModal()
        exit(1)
    }
}
```

这些示例为macOS应用程序提供了完整的许可证集成方案，包括硬件指纹获取、许可证激活验证、安全存储和防篡改检测等功能。开发者可以根据具体需求进行调整和扩展。
