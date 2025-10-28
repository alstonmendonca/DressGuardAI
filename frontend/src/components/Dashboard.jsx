import React, { useState, useEffect } from "react";
import { XIcon, TrashIcon, ChevronLeftIcon, ChevronRightIcon, CalendarIcon } from "./Icons";

export default function Dashboard({ isOpen, onClose }) {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [availableDates, setAvailableDates] = useState([]);
    const [total, setTotal] = useState(0);
    const perPage = 10;

    // Fetch logs when dashboard opens or filters change
    useEffect(() => {
        if (isOpen) {
            fetchLogs();
            fetchAvailableDates();
        }
    }, [isOpen, currentPage, selectedDate]);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const response = await fetch(`/api/dashboard/logs/?date=${selectedDate}&page=${currentPage}&per_page=${perPage}`);
            if (response.ok) {
                const data = await response.json();
                setLogs(data.logs);
                setTotalPages(data.total_pages);
                setTotal(data.total);
            } else {
                console.error("Failed to fetch logs");
            }
        } catch (err) {
            console.error("Error fetching logs:", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchAvailableDates = async () => {
        try {
            const response = await fetch("/api/dashboard/dates/");
            if (response.ok) {
                const data = await response.json();
                setAvailableDates(data.dates);
            }
        } catch (err) {
            console.error("Error fetching dates:", err);
        }
    };

    const handleDeleteLog = async (filename) => {
        if (!confirm(`Delete this log entry?`)) return;

        try {
            const response = await fetch(`/api/dashboard/log/${filename}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                // Refresh logs
                fetchLogs();
                fetchAvailableDates();
            } else {
                alert("Failed to delete log");
            }
        } catch (err) {
            console.error("Error deleting log:", err);
            alert("Error deleting log");
        }
    };

    const handleClearDay = async () => {
        if (!confirm(`Clear all logs for ${selectedDate}?`)) return;

        try {
            const response = await fetch(`/api/dashboard/logs/clear/${selectedDate}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                const data = await response.json();
                alert(`Deleted ${data.deleted_count} log(s)`);
                fetchLogs();
                fetchAvailableDates();
                setCurrentPage(1);
            } else {
                alert("Failed to clear logs");
            }
        } catch (err) {
            console.error("Error clearing logs:", err);
            alert("Error clearing logs");
        }
    };

    const handlePageChange = (newPage) => {
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage);
        }
    };

    const handleDateChange = (e) => {
        setSelectedDate(e.target.value);
        setCurrentPage(1); // Reset to first page when date changes
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="bg-green-950 border-2 border-green-500 rounded-lg w-full max-w-6xl max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-green-500">
                    <h2 className="text-xl font-bold text-green-300">Non-Compliance Dashboard</h2>
                    <button
                        onClick={onClose}
                        className="text-green-400 hover:text-green-200 transition"
                    >
                        <XIcon className="w-6 h-6" />
                    </button>
                </div>

                {/* Filters */}
                <div className="p-4 border-b border-green-700 bg-green-900 bg-opacity-30">
                    <div className="flex flex-wrap gap-4 items-center">
                        {/* Date Filter */}
                        <div className="flex items-center gap-2">
                            <CalendarIcon className="w-5 h-5 text-green-400" />
                            <label className="text-green-300 text-sm">Date:</label>
                            <input
                                type="date"
                                value={selectedDate}
                                onChange={handleDateChange}
                                className="bg-black border border-green-600 text-green-200 px-3 py-1 rounded text-sm focus:outline-none focus:border-green-400"
                            />
                        </div>

                        {/* Quick Date Selector */}
                        {availableDates.length > 0 && (
                            <div className="flex items-center gap-2">
                                <label className="text-green-300 text-sm">Quick:</label>
                                <select
                                    value={selectedDate}
                                    onChange={handleDateChange}
                                    className="bg-black border border-green-600 text-green-200 px-3 py-1 rounded text-sm focus:outline-none focus:border-green-400"
                                >
                                    {availableDates.map(date => (
                                        <option key={date} value={date}>
                                            {date === new Date().toISOString().split('T')[0] ? 'Today' : date}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* Total Count */}
                        <div className="ml-auto text-green-300 text-sm">
                            Total: <span className="font-bold">{total}</span> log(s)
                        </div>

                        {/* Clear Day Button */}
                        {total > 0 && (
                            <button
                                onClick={handleClearDay}
                                className="bg-red-900 border border-red-500 text-red-200 px-3 py-1 rounded text-sm hover:bg-red-800 transition flex items-center gap-2"
                            >
                                <TrashIcon className="w-4 h-4" />
                                Clear Day
                            </button>
                        )}
                    </div>
                </div>

                {/* Logs Grid */}
                <div className="flex-1 overflow-y-auto p-4">
                    {loading ? (
                        <div className="text-center text-green-300 py-8">Loading...</div>
                    ) : logs.length === 0 ? (
                        <div className="text-center text-green-400 py-8">
                            No logs found for {selectedDate}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {logs.map((log) => (
                                <div
                                    key={log.id}
                                    className="bg-black border border-green-600 rounded-lg overflow-hidden hover:border-green-400 transition"
                                >
                                    {/* Image */}
                                    <div className="relative bg-gray-900">
                                        <img
                                            src={log.image_url}
                                            alt={`Log ${log.id}`}
                                            className="w-full h-48 object-contain"
                                        />
                                        {/* Delete Button Overlay */}
                                        <button
                                            onClick={() => handleDeleteLog(log.filename)}
                                            className="absolute top-2 right-2 bg-red-900 bg-opacity-90 border border-red-500 text-red-200 p-2 rounded hover:bg-red-800 transition"
                                            title="Delete this log"
                                        >
                                            <TrashIcon className="w-4 h-4" />
                                        </button>
                                    </div>

                                    {/* Info */}
                                    <div className="p-3">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <div className="text-green-300 font-bold text-sm">
                                                    {log.person}
                                                </div>
                                                <div className="text-green-500 text-xs">
                                                    {log.timestamp}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Violations */}
                                        {log.violations && log.violations.length > 0 && (
                                            <div className="mt-2">
                                                <div className="text-red-400 text-xs font-semibold mb-1">
                                                    Non-Compliant Items:
                                                </div>
                                                <div className="flex flex-wrap gap-1">
                                                    {log.violations.map((item, idx) => (
                                                        <span
                                                            key={idx}
                                                            className="bg-red-900 border border-red-500 text-red-200 text-xs px-2 py-1 rounded"
                                                        >
                                                            {item}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="p-4 border-t border-green-700 bg-green-900 bg-opacity-30">
                        <div className="flex justify-center items-center gap-2">
                            <button
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                                className={`p-2 rounded border ${
                                    currentPage === 1
                                        ? 'bg-gray-800 border-gray-600 text-gray-500 cursor-not-allowed'
                                        : 'bg-black border-green-600 text-green-300 hover:border-green-400'
                                }`}
                            >
                                <ChevronLeftIcon className="w-5 h-5" />
                            </button>

                            <span className="text-green-300 text-sm">
                                Page {currentPage} of {totalPages}
                            </span>

                            <button
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                className={`p-2 rounded border ${
                                    currentPage === totalPages
                                        ? 'bg-gray-800 border-gray-600 text-gray-500 cursor-not-allowed'
                                        : 'bg-black border-green-600 text-green-300 hover:border-green-400'
                                }`}
                            >
                                <ChevronRightIcon className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
