import React, { useState, useEffect } from "react";
import { XIcon, FileTextIcon, CalendarIcon } from "./Icons";

export default function ReportGenerator({ isOpen, onClose }) {
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [selectedModel, setSelectedModel] = useState('');
    const [availableDates, setAvailableDates] = useState([]);
    const [availableModels, setAvailableModels] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [whatsappStatus, setWhatsappStatus] = useState({ enabled: false, configured: false });
    const [sendingWhatsapp, setSendingWhatsapp] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchAvailableDates();
            fetchAvailableModels();
            checkWhatsappStatus();
        }
    }, [isOpen]);

    const fetchAvailableModels = async () => {
        try {
            const response = await fetch("/api/dashboard/models/");
            if (response.ok) {
                const data = await response.json();
                setAvailableModels(data.models);
                // Set first model as default if available
                if (data.models.length > 0 && !selectedModel) {
                    setSelectedModel(data.models[0]);
                }
            }
        } catch (err) {
            console.error("Error fetching models:", err);
        }
    };

    const checkWhatsappStatus = async () => {
        try {
            const response = await fetch("/dashboard/whatsapp/status/");
            if (response.ok) {
                const data = await response.json();
                setWhatsappStatus(data);
            }
        } catch (err) {
            console.error("Error checking WhatsApp status:", err);
        }
    };

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
            const modelParam = (selectedModel && selectedModel !== 'all' && selectedModel !== '') ? `?model=${encodeURIComponent(selectedModel)}` : '';
            const response = await fetch(`/api/dashboard/report/${selectedDate}${modelParam}`);
            
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

    const handleModelChange = (e) => {
        setSelectedModel(e.target.value);
        setError(null);
    };

    const handleSendWhatsApp = async () => {
        setSendingWhatsapp(true);
        setError(null);

        try {
            const response = await fetch("/dashboard/send-whatsapp/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ 
                    date: selectedDate,
                    model: (selectedModel && selectedModel !== 'all' && selectedModel !== '') ? selectedModel : null
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to send WhatsApp notification');
            }

            // Show success message
            const successMsg = `✓ WhatsApp sent successfully!\n\nDate: ${data.date}\nViolations: ${data.violation_count}\nRecipients: ${data.successful_sends}/${data.total_recipients}`;
            alert(successMsg);

        } catch (err) {
            console.error("Error sending WhatsApp:", err);
            setError(err.message || 'Failed to send WhatsApp notification');
        } finally {
            setSendingWhatsapp(false);
        }
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
                    <div className="mb-4">
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

                    {/* Model Selection */}
                    <div className="mb-6">
                        <label className="block text-green-300 text-sm font-semibold mb-2">
                            Select Model:
                        </label>
                        <select
                            value={selectedModel}
                            onChange={handleModelChange}
                            className="w-full bg-black border border-green-600 text-green-200 px-3 py-2 rounded focus:outline-none focus:border-green-400"
                        >
                            {availableModels.map(model => (
                                <option key={model} value={model}>
                                    {model}
                                </option>
                            ))}
                        </select>
                        <p className="text-green-500 text-xs mt-1">
                            Reports will only include violations from the selected model
                        </p>
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
                            <li>• Detection model used</li>
                            <li>• License plates (for Vehicle Helmet model)</li>
                            <li>• Reference image filename</li>
                        </ul>
                        {selectedModel && (
                            <div className="mt-2 pt-2 border-t border-green-700">
                                <p className="text-yellow-400 text-xs">
                                    ⚠️ Filtering by: <span className="font-semibold">{selectedModel}</span>
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-col gap-3">
                        {/* Primary Action Buttons */}
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
                                disabled={loading || sendingWhatsapp}
                                className="px-4 py-2 bg-black border border-green-600 text-green-300 rounded hover:bg-green-900 transition disabled:opacity-50"
                            >
                                Cancel
                            </button>
                        </div>

                        {/* WhatsApp Button */}
                        {whatsappStatus.enabled && whatsappStatus.configured && (
                            <button
                                onClick={handleSendWhatsApp}
                                disabled={sendingWhatsapp || availableDates.length === 0}
                                className={`w-full py-2 px-4 rounded font-semibold flex items-center justify-center gap-2 transition ${
                                    sendingWhatsapp || availableDates.length === 0
                                        ? 'bg-gray-700 border border-gray-600 text-gray-400 cursor-not-allowed'
                                        : 'bg-green-600 border border-green-400 text-white hover:bg-green-500'
                                }`}
                            >
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                                </svg>
                                {sendingWhatsapp ? 'Sending to WhatsApp...' : 'Send Report via WhatsApp'}
                            </button>
                        )}

                        {/* WhatsApp Not Configured Message */}
                        {!whatsappStatus.configured && (
                            <p className="text-yellow-400 text-xs text-center">
                                💡 Configure Twilio credentials in config.py to enable WhatsApp reports
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
