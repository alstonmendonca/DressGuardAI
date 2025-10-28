import React, { useState, useEffect } from "react";
import { XIcon, FileTextIcon, CalendarIcon } from "./Icons";

export default function ReportGenerator({ isOpen, onClose }) {
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [availableDates, setAvailableDates] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen) {
            fetchAvailableDates();
        }
    }, [isOpen]);

    const fetchAvailableDates = async () => {
        try {
            const response = await fetch("/api/dashboard/dates/");
            if (response.ok) {
                const data = await response.json();
                setAvailableDates(data.dates);
                // Set selected date to first available if current date has no logs
                if (data.dates.length > 0 && !data.dates.includes(selectedDate)) {
                    setSelectedDate(data.dates[0]);
                }
            }
        } catch (err) {
            console.error("Error fetching dates:", err);
        }
    };

    const handleGenerateReport = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`/api/dashboard/report/${selectedDate}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate report');
            }

            // Get the blob from response
            const blob = await response.blob();
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            
            // Get filename from content-disposition header or use default
            const contentDisposition = response.headers.get('content-disposition');
            let filename = `DressGuard_Report_${selectedDate.replace(/-/g, '')}.xlsx`;
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }
            
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            
            // Cleanup
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            // Show success message
            alert(`Report generated successfully!\nFile: ${filename}`);
            
        } catch (err) {
            console.error("Error generating report:", err);
            setError(err.message || 'Failed to generate report');
        } finally {
            setLoading(false);
        }
    };

    const handleDateChange = (e) => {
        setSelectedDate(e.target.value);
        setError(null);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="bg-green-950 border-2 border-green-500 rounded-lg w-full max-w-md">
                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-green-500">
                    <div className="flex items-center gap-2">
                        <FileTextIcon className="w-6 h-6 text-green-300" />
                        <h2 className="text-xl font-bold text-green-300">Generate Report</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-green-400 hover:text-green-200 transition"
                    >
                        <XIcon className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    <p className="text-green-300 text-sm mb-4">
                        Select a date to generate an Excel report of all non-compliance violations for that day.
                    </p>

                    {/* Date Selection */}
                    <div className="mb-6">
                        <label className="block text-green-300 text-sm font-semibold mb-2">
                            Select Date:
                        </label>
                        
                        {/* Manual Date Picker */}
                        <div className="flex items-center gap-2 mb-3">
                            <CalendarIcon className="w-5 h-5 text-green-400" />
                            <input
                                type="date"
                                value={selectedDate}
                                onChange={handleDateChange}
                                className="flex-1 bg-black border border-green-600 text-green-200 px-3 py-2 rounded focus:outline-none focus:border-green-400"
                            />
                        </div>

                        {/* Quick Date Selector */}
                        {availableDates.length > 0 && (
                            <div>
                                <label className="block text-green-400 text-xs mb-1">
                                    Or choose from available dates:
                                </label>
                                <select
                                    value={selectedDate}
                                    onChange={handleDateChange}
                                    className="w-full bg-black border border-green-600 text-green-200 px-3 py-2 rounded focus:outline-none focus:border-green-400"
                                >
                                    {availableDates.map(date => (
                                        <option key={date} value={date}>
                                            {date === new Date().toISOString().split('T')[0] ? `${date} (Today)` : date}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {availableDates.length === 0 && (
                            <p className="text-yellow-400 text-xs mt-2">
                                No violation logs found. Start detecting to generate reports.
                            </p>
                        )}
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-500 rounded">
                            <p className="text-red-200 text-sm">{error}</p>
                        </div>
                    )}

                    {/* Report Details */}
                    <div className="bg-green-900 bg-opacity-30 border border-green-700 rounded p-3 mb-6">
                        <h3 className="text-green-300 text-sm font-semibold mb-2">Report will include:</h3>
                        <ul className="text-green-400 text-xs space-y-1">
                            <li>• Student full name and USN</li>
                            <li>• Department and branch</li>
                            <li>• Email address</li>
                            <li>• Violation timestamp</li>
                            <li>• Non-compliant items</li>
                            <li>• Reference image filename</li>
                        </ul>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                        <button
                            onClick={handleGenerateReport}
                            disabled={loading || availableDates.length === 0}
                            className={`flex-1 py-2 px-4 rounded font-semibold flex items-center justify-center gap-2 transition ${
                                loading || availableDates.length === 0
                                    ? 'bg-gray-700 border border-gray-600 text-gray-400 cursor-not-allowed'
                                    : 'bg-green-700 border border-green-500 text-green-100 hover:bg-green-600'
                            }`}
                        >
                            <FileTextIcon className="w-5 h-5" />
                            {loading ? 'Generating...' : 'Generate Excel Report'}
                        </button>
                        
                        <button
                            onClick={onClose}
                            disabled={loading}
                            className="px-4 py-2 bg-black border border-green-600 text-green-300 rounded hover:bg-green-900 transition disabled:opacity-50"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
