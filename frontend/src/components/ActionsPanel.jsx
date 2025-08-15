import React from "react";

export default function ActionsPanel(){
    return(
        <div className="row-start-2 bg-green-950 border border-green-500 p-4 rounded flex flex-col gap-3 h-full overflow-y-auto">
          <h3 className="text-center font-bold text-green-300 mb-4">Actions</h3>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            Change Model
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            📄 Generate Report
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            🔔 Set Alerts
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            📂 Save Session
          </button>
          <button className="bg-black border border-green-600 py-2 hover:bg-green-900 transition text-xs">
            History
          </button>
        </div>
    );
}