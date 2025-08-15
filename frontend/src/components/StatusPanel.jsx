import React from "react";

export default function StatusPanel(){
    return(
        <div className="row-start-2 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-4">System Status</h3>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            ✅ AI Model: Active
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            📶 Connection: Stable
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            💾 Storage: 42% Used
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            ⚙️ Resolution: 1080p
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs text-left pl-3">
            🕒 Uptime: 7h 24m
          </button>
        </div>
    );
}