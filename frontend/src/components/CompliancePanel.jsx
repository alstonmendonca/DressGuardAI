import React, { useState, useEffect } from "react";
import { CheckIcon, XIcon, CircleIcon, SaveIcon, RefreshIcon, ResetIcon } from "./Icons";

export default function CompliancePanel({ currentModel }) {
  const [config, setConfig] = useState(null);
  const [allClasses, setAllClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [saving, setSaving] = useState(false);

  // Fetch compliance config
  const fetchConfig = async () => {
    try {
      const response = await fetch("/api/compliance/config/");
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (err) {
      console.error("Failed to fetch compliance config:", err);
      setError("Failed to load compliance settings");
    }
  };

  // Fetch all detected classes from model
  const fetchAllClasses = async () => {
    try {
      const response = await fetch("/api/compliance/detected-classes/");
      if (response.ok) {
        const data = await response.json();
        // Use current_model_classes instead of all classes to show only the selected model's classes
        setAllClasses(data.current_model_classes || []);
        console.log("Loaded classes from current model:", data.current_model);
      }
    } catch (err) {
      console.error("Failed to fetch classes:", err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchConfig(), fetchAllClasses()]);
      setLoading(false);
    };
    loadData();
  }, [currentModel]); // Re-fetch when currentModel changes

  const toggleClass = (className, currentStatus) => {
    if (!config) return;

    const newConfig = { ...config };
    const lowerClassName = className.toLowerCase();

    // Cycle: neutral → compliant → non-compliant → neutral
    if (currentStatus === "neutral") {
      // Add to compliant
      if (!newConfig.compliant_classes.includes(lowerClassName)) {
        newConfig.compliant_classes.push(lowerClassName);
      }
    } else if (currentStatus === "compliant") {
      // Remove from compliant, add to non-compliant
      newConfig.compliant_classes = newConfig.compliant_classes.filter(
        (c) => c !== lowerClassName
      );
      if (!newConfig.non_compliant_classes.includes(lowerClassName)) {
        newConfig.non_compliant_classes.push(lowerClassName);
      }
    } else if (currentStatus === "non-compliant") {
      // Remove from non-compliant (back to neutral)
      newConfig.non_compliant_classes = newConfig.non_compliant_classes.filter(
        (c) => c !== lowerClassName
      );
    }

    setConfig(newConfig);
  };

  const saveConfig = async () => {
    if (!config) return;

    setSaving(true);
    try {
      const response = await fetch("/api/compliance/config/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          compliant_classes: config.compliant_classes,
          non_compliant_classes: config.non_compliant_classes,
          min_confidence: config.min_confidence || 0.5,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Saved compliance config:", data);
        alert("Compliance settings saved successfully!");
        await fetchConfig(); // Refresh to confirm
      } else {
        const errorData = await response.json();
        console.error("Save failed:", errorData);
        alert(`Failed to save: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Error saving compliance config:", err);
      alert("Error saving compliance settings: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    if (confirm("Reset to default compliance settings? This will restore config.py values.")) {
      // Reset to config.py defaults
      const defaultConfig = {
        compliant_classes: ["full sleeve shirt", "half sleeve shirt", "pants", "kurthi", "id card"],
        non_compliant_classes: ["t-shirt", "shorts", "tshirt", "tee shirt", "t shirt", "short pants", "short"],
        min_confidence: 0.5
      };
      setConfig(defaultConfig);
    }
  };

  const getClassStatus = (className) => {
    if (!config) return "neutral";
    const lowerClassName = className.toLowerCase();
    if (config.compliant_classes.includes(lowerClassName)) return "compliant";
    if (config.non_compliant_classes.includes(lowerClassName))
      return "non-compliant";
    return "neutral";
  };

  if (loading) {
    return (
      <div className="bg-green-950 border border-green-500 p-4 rounded">
        <h3 className="text-center font-bold text-green-300 mb-3">
          Compliance Settings
        </h3>
        <p className="text-green-400 text-center">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-green-950 border border-red-500 p-4 rounded">
        <h3 className="text-center font-bold text-red-300 mb-3">Error</h3>
        <p className="text-red-400 text-center text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-green-950 border border-green-500 p-3 rounded flex flex-col gap-2 h-full overflow-hidden">
      <div className="flex justify-between items-center">
        <h3 className="font-bold text-green-300 text-sm">
          Compliance Settings
          {currentModel && (
            <span className="text-[10px] text-green-400 ml-2 font-normal">
              ({currentModel})
            </span>
          )}
        </h3>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="bg-black border border-green-600 px-3 py-1 hover:bg-green-900 transition text-xs"
        >
          {showSettings ? "Hide" : "Configure"}
        </button>
      </div>

      {!showSettings ? (
        // Summary View
        <div className="flex flex-col gap-2 text-xs">
          <div className="bg-black border border-green-600 p-2 rounded">
            <p className="text-green-400 flex items-center gap-2">
              <CheckIcon className="w-3 h-3" /> Compliant: {config?.compliant_classes.length || 0}
            </p>
            <p className="text-red-400 flex items-center gap-2">
              <XIcon className="w-3 h-3" /> Non-Compliant: {config?.non_compliant_classes.length || 0}
            </p>
          </div>
        </div>
      ) : (
        // Detailed Settings View
        <div className="flex flex-col gap-2 overflow-y-auto flex-1">
          <div className="text-xs text-green-400 bg-black p-2 rounded">
            <p className="font-bold mb-1">Click to cycle status:</p>
            <p className="flex items-center gap-1">
              <CircleIcon className="w-3 h-3" /> Neutral → 
              <CheckIcon className="w-3 h-3" /> Compliant → 
              <XIcon className="w-3 h-3" /> Non-Compliant → 
              <CircleIcon className="w-3 h-3" /> Neutral
            </p>
          </div>

          <div className="flex flex-col gap-1 max-h-64 overflow-y-auto bg-black p-2 rounded">
            {allClasses.length === 0 ? (
              <p className="text-orange-400 text-center py-2">
                No classes available. Make sure a model is loaded.
              </p>
            ) : (
              allClasses.map((className) => {
                const status = getClassStatus(className);
                let bgColor = "bg-gray-700"; // neutral
                let textColor = "text-orange-300";
                let IconComponent = CircleIcon;

                if (status === "compliant") {
                  bgColor = "bg-green-900";
                  textColor = "text-green-300";
                  IconComponent = CheckIcon;
                } else if (status === "non-compliant") {
                  bgColor = "bg-red-900";
                  textColor = "text-red-300";
                  IconComponent = XIcon;
                }

                return (
                  <button
                    key={className}
                    onClick={() => toggleClass(className, status)}
                    className={`${bgColor} ${textColor} px-2 py-1 rounded text-xs text-left hover:opacity-80 transition flex justify-between items-center`}
                  >
                    <span>{className}</span>
                    <IconComponent className="w-3 h-3" />
                  </button>
                );
              })
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={saveConfig}
              disabled={saving}
              className="flex-1 bg-green-700 border border-green-500 py-2 hover:bg-green-600 transition text-xs font-bold disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <SaveIcon className="w-3 h-3" />
              {saving ? "Saving..." : "Save Settings"}
            </button>
            <button
              onClick={resetToDefaults}
              className="bg-orange-700 border border-orange-500 px-3 py-2 hover:bg-orange-600 transition text-xs flex items-center justify-center"
              title="Reset to defaults"
            >
              <ResetIcon className="w-4 h-4" />
            </button>
            <button
              onClick={fetchConfig}
              className="bg-black border border-green-600 px-3 py-2 hover:bg-green-900 transition text-xs flex items-center justify-center"
              title="Reload from server"
            >
              <RefreshIcon className="w-4 h-4" />
            </button>
          </div>

          {config && (
            <div className="text-xs bg-black p-2 rounded">
              <p className="text-green-400 flex items-center gap-1">
                <CheckIcon className="w-3 h-3" /> Compliant ({config.compliant_classes.length}):{" "}
                {config.compliant_classes.join(", ") || "None"}
              </p>
              <p className="text-red-400 mt-1 flex items-center gap-1">
                <XIcon className="w-3 h-3" /> Non-Compliant ({config.non_compliant_classes.length}):{" "}
                {config.non_compliant_classes.join(", ") || "None"}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
