/**
 * Highlight.js加载器
 * 用于确保highlight.js正确加载，处理不同版本和路径问题
 */
(function() {
    // 检查highlight.js是否已加载
    function checkHljs() {
        if (typeof hljs !== 'undefined') {
            // 已加载
            console.log('highlight.js已加载 - 版本兼容性处理');
            
            // 确保所有必要方法存在
            if (!hljs.highlightAll && typeof hljs.highlightBlock === 'function') {
                hljs.highlightAll = function() {
                    var blocks = document.querySelectorAll('pre code');
                    Array.prototype.forEach.call(blocks, hljs.highlightBlock);
                };
                console.log('添加highlightAll兼容方法');
            }
            
            // 应用高亮
            try {
                if (typeof hljs.highlightAll === 'function') {
                    hljs.highlightAll();
                } else if (typeof hljs.highlightBlock === 'function') {
                    var blocks = document.querySelectorAll('pre code');
                    Array.prototype.forEach.call(blocks, hljs.highlightBlock);
                } else if (typeof hljs.highlightElement === 'function') {
                    var blocks = document.querySelectorAll('pre code');
                    Array.prototype.forEach.call(blocks, hljs.highlightElement);
                }
                console.log('高亮应用成功');
                
                // 触发就绪事件
                document.dispatchEvent(new Event('highlightjsReady'));
            } catch (e) {
                console.error('高亮应用失败:', e);
                loadFallback();
            }
            
            return true;
        }
        
        return false;
    }
    
    // 加载备用版本
    function loadFallback() {
        console.warn('正在加载备用highlight.js版本');
        
        // 激活备用CSS
        var fallbackCss = document.getElementById('hljs-fallback-css');
        if (fallbackCss) {
            fallbackCss.disabled = false;
        }
        
        // 加载备用JS
        var script = document.createElement('script');
        script.src = '/static/js/highlight.min.js';
        script.onload = function() {
            console.log('备用highlight.js加载成功');
            if (typeof hljs !== 'undefined') {
                if (typeof hljs.highlightAll === 'function') {
                    hljs.highlightAll();
                } else {
                    var blocks = document.querySelectorAll('pre code');
                    Array.prototype.forEach.call(blocks, function(block) {
                        hljs.highlightElement(block);
                    });
                }
            }
        };
        document.body.appendChild(script);
    }
    
    // 在DOM加载完成后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            if (!checkHljs()) {
                // 如果未加载，尝试直接加载
                loadFallback();
            }
        });
    } else {
        // DOM已加载
        if (!checkHljs()) {
            // 如果未加载，尝试直接加载
            loadFallback();
        }
    }
})(); 