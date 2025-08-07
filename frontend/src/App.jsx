import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="h-screen w-screen bg-zinc-900 text-white font-sans grid grid-rows-[40px_1fr] grid-cols-[200px_1fr]">
      {/* Top Toolbar */}
      <div className="col-span-2 flex items-center justify-between px-4 bg-zinc-800 border-b border-zinc-700">
        <h1 className="text-lg font-bold">My Unity-Like App</h1>
        <div className="space-x-2">
          <button className="bg-zinc-700 hover:bg-zinc-600 px-3 py-1 rounded">Play</button>
          <button className="bg-zinc-700 hover:bg-zinc-600 px-3 py-1 rounded">Pause</button>
        </div>
      </div>

      {/* Sidebar */}
      <div className="bg-zinc-850 p-2 border-r border-zinc-700 flex flex-col gap-2">
        <div className="font-semibold text-sm">Hierarchy</div>
        <ul className="text-sm space-y-1">
          <li>📦 Main Camera</li>
          <li>🎮 Player</li>
          <li>🌍 Environment</li>
        </ul>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-2 grid-rows-2 gap-2 p-2">
        {/* Scene View */}
        <div className="bg-zinc-800 border border-zinc-700 rounded p-2">
          <h2 className="text-sm font-semibold mb-2">Scene</h2>
          <div className="h-full bg-zinc-900 border border-dashed border-zinc-600 rounded"></div>
        </div>

        {/* Game View */}
        <div className="bg-zinc-800 border border-zinc-700 rounded p-2">
          <h2 className="text-sm font-semibold mb-2">Game</h2>
          <div className="h-full bg-zinc-900 border border-dashed border-zinc-600 rounded"></div>
        </div>

        {/* Inspector */}
        <div className="bg-zinc-800 border border-zinc-700 rounded p-2 col-span-2">
          <h2 className="text-sm font-semibold mb-2">Inspector</h2>
          <div className="flex flex-col gap-2 text-sm">
            <div>Name: <span className="text-zinc-400">Player</span></div>
            <div>Position: <span className="text-zinc-400">X: 0, Y: 0, Z: 0</span></div>
            <div>Health: <span className="text-zinc-400">{count}</span></div>
            <button
              onClick={() => setCount((c) => c + 1)}
              className="mt-2 bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded w-max"
            >
              Increase Health
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
