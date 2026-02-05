#!/usr/bin/env python3
# -*- coding: utf-8 -*-

remaining_content = '''
    
    private val vertexShader = """
        attribute vec4 aPosition;
        attribute vec4 aTextureCoord;
        uniform mat4 uTextureMatrix;
        varying vec2 vTextureCoord;
        
        void main() {
            gl_Position = aPosition;
            vTextureCoord = (uTextureMatrix * aTextureCoord).xy;
        }
    """.trimIndent()
    
    private val fragmentShader = """
        #extension GL_OES_EGL_image_external : require
        precision mediump float;
        varying vec2 vTextureCoord;
        uniform samplerExternalOES sTexture;
        
        void main() {
            gl_FragColor = texture2D(sTexture, vTextureCoord);
        }
    """.trimIndent()
    
    fun drawFrame(textureId: Int, transformMatrix: FloatArray) {
        GLES20.glClearColor(0.0f, 0.0f, 0.0f, 1.0f)
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT)
        GLES20.glUseProgram(program)
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
        GLES20.glBindTexture(textureTarget, textureId)
        // ... 绘制逻辑
    }
    
    fun release() {
        GLES20.glDeleteProgram(program)
    }
}</code></pre>
                </div>
            </section>

            <!-- 第六部分:视频编辑 -->
            <section id="editing">
                <h2>六、视频编辑功能</h2>

                <h3>6.1 视频编辑架构</h3>
                <p>视频编辑需要解码源视频,进行处理(裁剪、滤镜、特效等),然后重新编码。</p>

                <div class="flow-diagram">
                    <div class="flow-step">源视频</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">MediaExtractor</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">MediaCodec解码</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">OpenGL处理</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">MediaCodec编码</div>
                    <span class="flow-arrow">→</span>
                    <div class="flow-step">输出视频</div>
                </div>

                <h3>6.2 完整使用示例</h3>
                <div class="code-block">
                    <div class="code-title">Kotlin - Activity中使用录制功能</div>
                    <pre><code>class CameraActivity : AppCompatActivity() {
    private lateinit var videoRecorder: VideoRecorder
    private var isRecording = false
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_camera)
        
        videoRecorder = VideoRecorder(this, 1920, 1080, 30)
        
        findViewById&lt;Button&gt;(R.id.btnRecord).setOnClickListener {
            if (isRecording) stopRecording() else startRecording()
        }
    }
    
    private fun startRecording() {
        val outputFile = File(
            getExternalFilesDir(Environment.DIRECTORY_MOVIES),
            "video_${System.currentTimeMillis()}.mp4"
        )
        videoRecorder.prepare(outputFile.absolutePath)
        videoRecorder.startRecording()
        isRecording = true
    }
    
    private fun stopRecording() {
        videoRecorder.stopRecording {
            isRecording = false
            Toast.makeText(this, "录制完成", Toast.LENGTH_SHORT).show()
        }
    }
}</code></pre>
                </div>
            </section>

            <!-- 第七部分:最佳实践 -->
            <section id="best-practices">
                <h2>七、最佳实践与优化建议</h2>

                <h3>7.1 性能优化</h3>
                <div class="tip-box">
                    <strong>💡 优化建议</strong>
                    <ul>
                        <li><strong>使用硬件编码:</strong> 优先选择硬件编码器,性能提升显著</li>
                        <li><strong>合理设置码率:</strong> 1080p@30fps建议6-8Mbps,720p@30fps建议3-5Mbps</li>
                        <li><strong>I帧间隔:</strong> 建议设置为1-2秒,平衡文件大小和随机访问性能</li>
                        <li><strong>使用CBR模式:</strong> 恒定码率模式适合实时录制,文件大小可预测</li>
                        <li><strong>避免内存拷贝:</strong> 使用Surface-to-Surface链路,减少CPU参与</li>
                    </ul>
                </div>

                <h3>7.2 常见问题处理</h3>
                <table>
                    <thead>
                        <tr>
                            <th>问题</th>
                            <th>原因</th>
                            <th>解决方案</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>画面旋转错误</td>
                            <td>未正确处理传感器方向</td>
                            <td>根据SENSOR_ORIENTATION调整变换矩阵</td>
                        </tr>
                        <tr>
                            <td>编码延迟高</td>
                            <td>输出缓冲区未及时释放</td>
                            <td>及时调用drainEncoder()处理输出数据</td>
                        </tr>
                        <tr>
                            <td>颜色异常</td>
                            <td>颜色空间转换问题</td>
                            <td>使用TEXTURE_EXTERNAL_OES纹理格式</td>
                        </tr>
                        <tr>
                            <td>音视频不同步</td>
                            <td>时间戳设置不正确</td>
                            <td>使用统一的时间基准</td>
                        </tr>
                        <tr>
                            <td>内存泄漏</td>
                            <td>资源未正确释放</td>
                            <td>及时释放MediaCodec、Surface、EGL资源</td>
                        </tr>
                    </tbody>
                </table>

                <h3>7.3 关键代码检查清单</h3>
                <div class="important-box">
                    <strong>⚠️ 必做检查项</strong>
                    <ol>
                        <li>✓ MediaCodec配置FLAG_ENCODE标志</li>
                        <li>✓ InputSurface设置EGL_RECORDABLE_ANDROID属性</li>
                        <li>✓ 正确设置presentationTime(纳秒级)</li>
                        <li>✓ 处理BUFFER_FLAG_END_OF_STREAM标志</li>
                        <li>✓ MediaMuxer在收到格式变化后才start()</li>
                        <li>✓ 所有OpenGL操作在正确的线程执行</li>
                        <li>✓ 释放资源的顺序:先stop()再release()</li>
                    </ol>
                </div>

                <h3>7.4 完整数据流示意图</h3>
                <div class="code-block">
                    <div class="code-title">完整数据流</div>
                    <pre><code>Camera2 API
    ↓ (Image Stream)
SurfaceTexture (OES Texture)
    ↓ (updateTexImage)
OpenGL Thread
    ├→ Apply Filters/Effects
    └→ Render to InputSurface
        ↓ (eglSwapBuffers)
MediaCodec Encoder
    ↓ (Encoded Data)
MediaMuxer
    ↓ (Mux Audio + Video)
MP4 File</code></pre>
                </div>

                <div class="warning-box">
                    <strong>⚡ 线程模型注意事项</strong>
                    <ul>
                        <li><strong>相机回调:</strong> 在Camera Handler线程</li>
                        <li><strong>OpenGL操作:</strong> 必须在EGL上下文所在的GL线程</li>
                        <li><strong>编码器操作:</strong> 可在任意线程,但建议使用专用线程</li>
                        <li><strong>Muxer操作:</strong> 必须在同一线程完成</li>
                    </ul>
                </div>

                <h3>7.5 扩展功能建议</h3>
                <div class="info-box">
                    <strong>🚀 进阶功能</strong>
                    <ul>
                        <li><strong>实时美颜:</strong> 使用GPUImage或自定义Fragment Shader实现</li>
                        <li><strong>水印添加:</strong> 在OpenGL渲染阶段叠加纹理</li>
                        <li><strong>变速录制:</strong> 调整presentationTime实现慢动作/快动作</li>
                        <li><strong>多轨道合成:</strong> MediaMuxer支持多音频/视频轨道</li>
                        <li><strong>H.265编码:</strong> 使用"video/hevc" MIME类型,文件更小</li>
                        <li><strong>硬件加速滤镜:</strong> RenderScript或Vulkan实现高性能处理</li>
                    </ul>
                </div>

                <h3>7.6 参考资源</h3>
                <ul>
                    <li><strong>官方文档:</strong> <a href="https://developer.android.com/reference/android/hardware/camera2/package-summary" target="_blank">Camera2 API</a></li>
                    <li><strong>MediaCodec指南:</strong> <a href="https://developer.android.com/reference/android/media/MediaCodec" target="_blank">MediaCodec Reference</a></li>
                    <li><strong>开源项目:</strong> Grafika (Google官方示例)</li>
                    <li><strong>最佳实践:</strong> Android CTS测试用例参考</li>
                </ul>
            </section>
        </main>

        <button class="back-to-top" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">↑</button>
    </div>

    <script>
        // 返回顶部按钮显示控制
        window.addEventListener('scroll', function() {
            const backToTop = document.querySelector('.back-to-top');
            if (window.pageYOffset > 300) {
                backToTop.classList.add('show');
            } else {
                backToTop.classList.remove('show');
            }
        });

        // 平滑滚动
        document.querySelectorAll('nav a').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    </script>
</body>
</html>
'''

file_path = '/Users/master/Documents/project/knowelage/-/Android/Android-Camera2视频录制与编辑完全指南.html'

with open(file_path, 'a', encoding='utf-8') as f:
    f.write(remaining_content)

print("Content appended successfully!")
