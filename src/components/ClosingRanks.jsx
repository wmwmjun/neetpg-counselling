import { useState, useMemo, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { ChevronDown, Download, HelpCircle, ChevronUp, ChevronsUpDown } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import './ClosingRanks.css'
import closingRanksData from '../data/closingRanks.json'

const mockClosingRanks = closingRanksData

// Parse a formatted value like "1,23,456" or "-" to number. "-" → 0.
function parseVal(str) {
    if (!str || str === '-') return 0
    const n = parseInt(String(str).replace(/[₹,]/g, ''), 10)
    return isNaN(n) ? 0 : n
}

// Extract plain rank integer from entry (supports both [rank, candidateCat] and plain rank)
function rankVal(entry) {
    return Array.isArray(entry) ? entry[0] : entry
}

// Extract candidate category from entry (supports both [rank, candidateCat] and plain rank)
function candidateCatVal(entry, fallback) {
    return Array.isArray(entry) ? entry[1] : fallback
}

// Get the closing rank (last element) of a round, or null if no data
function closingRankOf(item, round) {
    const ranks = item.ranks?.[round]
    return ranks && ranks.length > 0 ? rankVal(ranks[ranks.length - 1]) : null
}

// All possible rounds per year (including future rounds not yet imported)
const YEAR_ROUNDS = {
    '2025': ['2025_R1', '2025_R2', '2025_R3', '2025_R4'],
    '2024': ['2024_R1', '2024_R2', '2024_R3', '2024_R4', '2024_R5'],
    '2023': ['2023_R1', '2023_R2', '2023_R3', '2023_R4', '2023_R5'],
}

// Short labels shown in table column headers
const ROUND_SHORT = {
    '2025_R1': 'R1', '2025_R2': 'R2', '2025_R3': 'R3', '2025_R4': 'Stray',
    '2024_R1': 'R1', '2024_R2': 'R2', '2024_R3': 'R3', '2024_R4': 'Stray', '2024_R5': 'Spec.',
    '2023_R1': 'R1', '2023_R2': 'R2', '2023_R3': 'R3', '2023_R4': 'Stray', '2023_R5': 'Spec.',
}

// Full labels used in detail modal
const ROUND_FULL = {
    '2025_R1': '2025 Round 1', '2025_R2': '2025 Round 2',
    '2025_R3': '2025 Round 3 (Mop-up)', '2025_R4': '2025 Stray Vacancy',
    '2024_R1': '2024 Round 1', '2024_R2': '2024 Round 2',
    '2024_R3': '2024 Round 3 (Mop-up)', '2024_R4': '2024 Stray Vacancy', '2024_R5': '2024 Special Stray',
    '2023_R1': '2023 Round 1', '2023_R2': '2023 Round 2',
    '2023_R3': '2023 Round 3 (Mop-up)', '2023_R4': '2023 Stray Vacancy', '2023_R5': '2023 Special Stray',
}

export default function ClosingRanks() {
    const [selectedYear, setSelectedYear] = useState('2025')
    const [filters, setFilters] = useState({
        rankFrom: '', rankTo: '',
        feeFrom: '', feeTo: '',
        stipendFrom: '', stipendTo: '',
        bondPenaltyFrom: '', bondPenaltyTo: '',
        bondYears: 'Select...',
        quota: 'Select...', category: 'Select...',
        state: 'Select...', course: 'Select...',
    })
    const [instituteSearch, setInstituteSearch] = useState('')
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [sortConfig, setSortConfig] = useState({ field: null, dir: 'asc' })
    const [selectedDetail, setSelectedDetail] = useState(null)
    const [currentPage, setCurrentPage] = useState(1)
    const itemsPerPage = 50

    // Rounds that actually have data for the currently selected year
    const visibleRounds = useMemo(() => {
        const candidates = YEAR_ROUNDS[selectedYear] || []
        return candidates.filter(r => mockClosingRanks.some(x => x.ranks?.[r]?.length > 0))
    }, [selectedYear])

    // Seat count per year (for tab badges)
    const yearCounts = useMemo(() => {
        const counts = {}
        for (const yr of Object.keys(YEAR_ROUNDS)) {
            const rounds = YEAR_ROUNDS[yr]
            counts[yr] = mockClosingRanks.filter(x => rounds.some(r => x.ranks?.[r]?.length > 0)).length
        }
        return counts
    }, [])

    // Dynamically build filter options from data
    const filterOptions = useMemo(() => {
        const quotas = new Set(), categories = new Set(), states = new Set(),
            courses = new Set(), bondYearsSet = new Set()
        mockClosingRanks.forEach(item => {
            if (item.quota) quotas.add(item.quota)
            if (item.category) categories.add(item.category)
            if (item.state) states.add(item.state)
            if (item.course) courses.add(item.course)
            if (item.bondYears && item.bondYears !== '-') bondYearsSet.add(item.bondYears)
        })
        return {
            quotas: Array.from(quotas).sort(),
            categories: Array.from(categories).sort(),
            states: Array.from(states).sort(),
            courses: Array.from(courses).sort(),
            bondYears: Array.from(bondYearsSet).sort((a, b) => Number(a) - Number(b)),
        }
    }, [])

    // Institute autocomplete suggestions
    const instituteSuggestions = useMemo(() => {
        const q = instituteSearch.trim().toLowerCase()
        if (!q) return []
        const seen = new Set()
        const results = []
        for (const item of mockClosingRanks) {
            if (item.institute && item.institute.toLowerCase().includes(q) && !seen.has(item.institute)) {
                seen.add(item.institute)
                results.push(item.institute)
                if (results.length >= 10) break
            }
        }
        return results
    }, [instituteSearch])

    // --- Filtering ---
    const filteredData = useMemo(() => {
        return mockClosingRanks.filter(item => {
            // Only show entries that have data in the selected year
            const hasYearData = visibleRounds.some(r => item.ranks?.[r]?.length > 0)
            if (!hasYearData) return false

            // Closing rank: use last rank across selected year's rounds
            const allRanks = visibleRounds.flatMap(r => (item.ranks?.[r] || []).map(rankVal))
            const lastRank = allRanks.length > 0 ? allRanks[allRanks.length - 1] : 0
            if (filters.rankFrom && lastRank < parseInt(filters.rankFrom)) return false
            if (filters.rankTo && lastRank > parseInt(filters.rankTo)) return false

            // Fee — treat "-" as 0; filter only applies when user entered a value
            const feeVal = parseVal(item.fee)
            if (filters.feeFrom && feeVal < parseInt(filters.feeFrom)) return false
            if (filters.feeTo && feeVal > parseInt(filters.feeTo)) return false

            // Stipend — treat "-" as 0
            const stipendVal = parseVal(item.stipend)
            if (filters.stipendFrom && stipendVal < parseInt(filters.stipendFrom)) return false
            if (filters.stipendTo && stipendVal > parseInt(filters.stipendTo)) return false

            // Bond Penalty — treat "-" as 0 (was missing before)
            const bpVal = parseVal(item.bondPenalty)
            if (filters.bondPenaltyFrom && bpVal < parseInt(filters.bondPenaltyFrom)) return false
            if (filters.bondPenaltyTo && bpVal > parseInt(filters.bondPenaltyTo)) return false

            // Bond Years dropdown
            if (filters.bondYears !== 'Select...' && String(item.bondYears) !== filters.bondYears) return false

            // Dropdown filters
            if (filters.quota !== 'Select...' && item.quota !== filters.quota) return false
            if (filters.category !== 'Select...' && item.category !== filters.category) return false
            if (filters.state !== 'Select...' && item.state !== filters.state) return false
            if (filters.course !== 'Select...' && item.course !== filters.course) return false

            // Institute search (case-insensitive partial match)
            if (instituteSearch.trim()) {
                const q = instituteSearch.trim().toLowerCase()
                if (!item.institute.toLowerCase().includes(q)) return false
            }

            return true
        })
    }, [filters, visibleRounds, instituteSearch])

    // --- Sorting ---
    const sortedData = useMemo(() => {
        if (!sortConfig.field) return filteredData
        return [...filteredData].sort((a, b) => {
            const { field, dir } = sortConfig
            let av, bv

            if (['fee', 'stipend', 'bondPenalty'].includes(field)) {
                av = parseVal(a[field]); bv = parseVal(b[field])
            } else if (field === 'bondYears') {
                av = a.bondYears === '-' ? -1 : Number(a.bondYears)
                bv = b.bondYears === '-' ? -1 : Number(b.bondYears)
            } else if (visibleRounds.includes(field)) {
                // Sort by closing rank of that round; null (no data) sorts to end
                av = closingRankOf(a, field) ?? (dir === 'asc' ? Infinity : -Infinity)
                bv = closingRankOf(b, field) ?? (dir === 'asc' ? Infinity : -Infinity)
            } else {
                av = String(a[field] ?? ''); bv = String(b[field] ?? '')
                return dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
            }
            return dir === 'asc' ? av - bv : bv - av
        })
    }, [filteredData, sortConfig])

    useEffect(() => { setCurrentPage(1) }, [filters, sortConfig, instituteSearch])
    useEffect(() => {
        setCurrentPage(1)
        setSortConfig({ field: null, dir: 'asc' })
    }, [selectedYear])

    const paginatedData = useMemo(() => {
        const start = (currentPage - 1) * itemsPerPage
        return sortedData.slice(start, start + itemsPerPage)
    }, [sortedData, currentPage])

    const totalPages = Math.ceil(sortedData.length / itemsPerPage)

    const handleInputChange = (field, value) => setFilters(prev => ({ ...prev, [field]: value }))

    const handleSort = (field) => {
        setSortConfig(prev =>
            prev.field === field
                ? { field, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
                : { field, dir: 'asc' }
        )
    }

    const clearFilters = () => {
        setFilters({
            rankFrom: '', rankTo: '', feeFrom: '', feeTo: '',
            stipendFrom: '', stipendTo: '', bondPenaltyFrom: '', bondPenaltyTo: '',
            bondYears: 'Select...', quota: 'Select...', category: 'Select...',
            state: 'Select...', course: 'Select...',
        })
        setInstituteSearch('')
    }

    const SortIcon = ({ field }) => {
        if (sortConfig.field !== field) return <ChevronsUpDown size={12} style={{ opacity: 0.35, marginLeft: 3 }} />
        return sortConfig.dir === 'asc'
            ? <ChevronUp size={12} style={{ marginLeft: 3, color: '#60a5fa' }} />
            : <ChevronDown size={12} style={{ marginLeft: 3, color: '#60a5fa' }} />
    }

    const thStyle = (field) => ({
        cursor: 'pointer',
        userSelect: 'none',
        color: sortConfig.field === field ? '#60a5fa' : undefined,
    })

    const renderRankCell = (item, round) => {
        const ranks = item.ranks?.[round]
        if (!ranks || ranks.length === 0) return <span style={{ color: 'var(--text-muted)' }}>-</span>
        const closingRank = rankVal(ranks[ranks.length - 1])
        return (
            <div className="rank-cell-content" style={{ cursor: 'pointer' }}
                onClick={() => setSelectedDetail({ item, round, ranks })}>
                <span className="closing-rank">{closingRank}</span>
                <span className="seat-count">({ranks.length})</span>
            </div>
        )
    }

    return (
        <>
            <div className="discovery-container">
                <div className="discovery-header">
                    <div className="breadcrumb">Discover / <strong>Closing Ranks</strong></div>
                    <button className="help-btn"><HelpCircle size={16} /> Help</button>
                </div>

                {/* Year tabs */}
                <div className="year-tabs">
                    {Object.keys(YEAR_ROUNDS).sort().reverse().map(yr => {
                        const count = yearCounts[yr]
                        const hasData = count > 0
                        return (
                            <button
                                key={yr}
                                className={`year-tab ${selectedYear === yr ? 'active' : ''} ${!hasData ? 'empty' : ''}`}
                                onClick={() => setSelectedYear(yr)}
                            >
                                {yr}
                                {hasData
                                    ? <span className="year-tab-count">{count.toLocaleString()}</span>
                                    : <span className="year-tab-no-data">データなし</span>
                                }
                            </button>
                        )
                    })}
                    <span className="year-tabs-hint">
                        {yearCounts['2024'] === 0 || yearCounts['2023'] === 0
                            ? '　2024・2023年のデータを追加: npm run update-historical'
                            : ''}
                    </span>
                </div>

                <div className="filter-panel glass-panel">
                    <div className="filter-grid">
                        <div className="filter-group">
                            <label>Closing Rank</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="1" value={filters.rankFrom} onChange={e => handleInputChange('rankFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="230087" value={filters.rankTo} onChange={e => handleInputChange('rankTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Fee (₹)</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="0" value={filters.feeFrom} onChange={e => handleInputChange('feeFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="22950000" value={filters.feeTo} onChange={e => handleInputChange('feeTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Stipend (₹)</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="0" value={filters.stipendFrom} onChange={e => handleInputChange('stipendFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="1560000" value={filters.stipendTo} onChange={e => handleInputChange('stipendTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Bond Penalty (₹)</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="0" value={filters.bondPenaltyFrom} onChange={e => handleInputChange('bondPenaltyFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="25000000" value={filters.bondPenaltyTo} onChange={e => handleInputChange('bondPenaltyTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Bond Years</label>
                            <div className="select-wrapper">
                                <select value={filters.bondYears} onChange={e => handleInputChange('bondYears', e.target.value)}>
                                    <option value="Select...">Select...</option>
                                    {filterOptions.bondYears.map(y => (
                                        <option key={y} value={y}>{y} {Number(y) === 1 ? 'Year' : 'Years'}</option>
                                    ))}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Quota</label>
                            <div className="select-wrapper">
                                <select value={filters.quota} onChange={e => handleInputChange('quota', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.quotas.map(q => <option key={q}>{q}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Category</label>
                            <div className="select-wrapper">
                                <select value={filters.category} onChange={e => handleInputChange('category', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.categories.map(c => <option key={c}>{c}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>State</label>
                            <div className="select-wrapper">
                                <select value={filters.state} onChange={e => handleInputChange('state', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.states.map(s => <option key={s}>{s}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group" style={{ justifyContent: 'flex-end', paddingTop: '1.5rem' }}>
                            <button className="clear-filter" onClick={clearFilters}>
                                <Download size={16} /> Clear Filters
                            </button>
                        </div>

                        <div className="filter-group full-width">
                            <label>Institute</label>
                            <div style={{ position: 'relative' }}>
                                <input
                                    type="text"
                                    placeholder="Type to search institute..."
                                    value={instituteSearch}
                                    onChange={e => { setInstituteSearch(e.target.value); setShowSuggestions(true) }}
                                    onFocus={() => setShowSuggestions(true)}
                                    onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                                    style={{ width: '100%', boxSizing: 'border-box' }}
                                />
                                {showSuggestions && instituteSuggestions.length > 0 && (
                                    <ul style={{
                                        position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
                                        background: 'var(--bg-card, #1e293b)', border: '1px solid var(--border, #334155)',
                                        borderRadius: '0.375rem', marginTop: 2, padding: 0,
                                        listStyle: 'none', maxHeight: '220px', overflowY: 'auto',
                                        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
                                    }}>
                                        {instituteSuggestions.map(name => (
                                            <li
                                                key={name}
                                                onMouseDown={() => { setInstituteSearch(name); setShowSuggestions(false) }}
                                                style={{
                                                    padding: '0.45rem 0.75rem', cursor: 'pointer',
                                                    fontSize: '0.8rem', borderBottom: '1px solid var(--border, #334155)',
                                                }}
                                                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover, #334155)'}
                                                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                            >
                                                {name}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>

                        <div className="filter-group full-width">
                            <label>Course</label>
                            <div className="select-wrapper">
                                <select value={filters.course} onChange={e => handleInputChange('course', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.courses.map(c => <option key={c}>{c}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="data-info">
                    <span>
                        Showing <strong>{Math.min((currentPage - 1) * itemsPerPage + 1, sortedData.length)} – {Math.min(currentPage * itemsPerPage, sortedData.length)}</strong> of <strong>{sortedData.length}</strong> matches.
                        {' '}(Total: {mockClosingRanks.length})
                    </span>
                    {sortConfig.field && (
                        <span style={{ fontSize: '0.75rem', color: '#60a5fa' }}>
                            Sorted by <strong>{sortConfig.field}</strong> ({sortConfig.dir})
                            <button onClick={() => setSortConfig({ field: null, dir: 'asc' })}
                                style={{ marginLeft: 8, color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.75rem' }}>
                                ✕ clear
                            </button>
                        </span>
                    )}
                </div>

                <div className="ranks-table-wrapper glass-panel">
                    <table className="ranks-table">
                        <thead>
                            <tr>
                                <th>Quota</th>
                                <th>Category</th>
                                <th>State</th>
                                <th>Institute</th>
                                <th>Course</th>
                                <th style={thStyle('fee')} onClick={() => handleSort('fee')}>
                                    Fee <SortIcon field="fee" />
                                </th>
                                <th style={thStyle('stipend')} onClick={() => handleSort('stipend')}>
                                    Stipend <SortIcon field="stipend" />
                                </th>
                                <th style={thStyle('bondPenalty')} onClick={() => handleSort('bondPenalty')}>
                                    Bond Penalty <SortIcon field="bondPenalty" />
                                </th>
                                <th style={thStyle('bondYears')} onClick={() => handleSort('bondYears')}>
                                    Bond Yrs <SortIcon field="bondYears" />
                                </th>
                                {visibleRounds.map(r => (
                                    <th key={r} style={thStyle(r)} onClick={() => handleSort(r)}>
                                        {ROUND_SHORT[r] ?? r} <SortIcon field={r} />
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {paginatedData.map((item, idx) => (
                                <tr key={item.id || idx}>
                                    <td>{item.quota}</td>
                                    <td>{item.category}</td>
                                    <td>{item.state}</td>
                                    <td className="inst-name">{item.institute}</td>
                                    <td>{item.course}</td>
                                    <td>{item.fee}</td>
                                    <td>{item.stipend}</td>
                                    <td>{item.bondPenalty}</td>
                                    <td>{item.bondYears}</td>
                                    {visibleRounds.map(r => (
                                        <td key={r} className="rank-highlight">{renderRankCell(item, r)}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {totalPages > 1 && (
                    <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1.5rem', paddingBottom: '2rem', flexShrink: 0 }}>
                        <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}
                            style={{ padding: '0.5rem 1rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--panel-bg)', cursor: currentPage === 1 ? 'not-allowed' : 'pointer', opacity: currentPage === 1 ? 0.5 : 1, color: 'var(--text-primary)' }}>
                            Previous
                        </button>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                            Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
                        </span>
                        <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}
                            style={{ padding: '0.5rem 1rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--panel-bg)', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer', opacity: currentPage === totalPages ? 0.5 : 1, color: 'var(--text-primary)' }}>
                            Next
                        </button>
                    </div>
                )}
            </div>

            {selectedDetail && createPortal(
                <AnimatePresence mode="wait">
                    <div className="modal-overlay" onClick={() => setSelectedDetail(null)}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 10 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 10 }}
                            transition={{ duration: 0.2 }}
                            className="modal-content"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="modal-header">
                                <h3>Allotment Details</h3>
                                <button className="close-btn" onClick={() => setSelectedDetail(null)}>×</button>
                            </div>
                            <div className="modal-body">
                                <div className="detail-info">
                                    <p><strong>Institute</strong><span>{selectedDetail.item.institute}</span></p>
                                    <p><strong>Course</strong><span>{selectedDetail.item.course}</span></p>
                                    <p><strong>Round</strong><span>{ROUND_FULL[selectedDetail.round] ?? selectedDetail.round}</span></p>
                                    <p><strong>Total Allotments</strong><span>{selectedDetail.ranks.length}</span></p>
                                </div>
                                <table className="allotment-list-table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>State</th>
                                            <th>Institute</th>
                                            <th>Course</th>
                                            <th>Quota</th>
                                            <th>Allotted Cat.</th>
                                            <th title="Candidate's own category (may differ from allotted seat category)">Candidate Cat. ⓘ</th>
                                            <th>AI Rank</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {selectedDetail.ranks.map((entry, index) => {
                                            const rank = rankVal(entry)
                                            const ccat = candidateCatVal(entry, selectedDetail.item.category)
                                            const isSameCat = ccat === selectedDetail.item.category
                                            return (
                                                <tr key={index}>
                                                    <td>{index + 1}</td>
                                                    <td>{selectedDetail.item.state}</td>
                                                    <td>{selectedDetail.item.institute}</td>
                                                    <td>{selectedDetail.item.course}</td>
                                                    <td>{selectedDetail.item.quota}</td>
                                                    <td>{selectedDetail.item.category}</td>
                                                    <td style={{ color: isSameCat ? 'inherit' : 'var(--accent-blue, #60a5fa)', fontStyle: isSameCat ? 'normal' : 'italic' }}>
                                                        {ccat}
                                                    </td>
                                                    <td className="rank-highlight">{rank}</td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </motion.div>
                    </div>
                </AnimatePresence>,
                document.body
            )}
        </>
    )
}
