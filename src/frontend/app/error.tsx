"use client";

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="zh-CN">
      <body>
        <main>
          <h1>页面加载失败</h1>
          <p>后端服务暂时不可用，请稍后再试。</p>
          <p>{error.message}</p>
          <button type="button" onClick={reset}>
            重试
          </button>
        </main>
      </body>
    </html>
  );
}
