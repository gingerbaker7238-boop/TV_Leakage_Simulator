import './App.css'

function App() {
  return (
    <main className="app-shell">
      <section className="foundation-card" aria-labelledby="app-title">
        <p className="eyebrow">Framework migration workspace</p>
        <h1 id="app-title">TV Leakage Simulator</h1>
        <p className="summary">
          Vite, React, TypeScript 기반의 차세대 프론트엔드가 준비되었습니다.
        </p>
        <div className="stack" aria-label="현재 구성된 프론트엔드 기술">
          <span>Vite</span>
          <span>React</span>
          <span>TypeScript</span>
        </div>
        <p className="next-step">
          다음 단계에서 디자인 토큰과 UI 컴포넌트 기반을 구성합니다.
        </p>
      </section>
    </main>
  )
}

export default App
