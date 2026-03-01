import { useState, useMemo } from 'react'
import { Search, ChevronDown, MapPin, BookOpen, TrendingUp, IndianRupee } from 'lucide-react'
import { motion } from 'framer-motion'
import instituteData from '../data/instituteStats.json'

const STATES = [...new Set(instituteData.map(i => i.state))].sort()

export default function CollegeFinder() {
    const [search, setSearch] = useState('')
    const [stateFilter, setStateFilter] = useState('All')
    const [feeFilter, setFeeFilter] = useState('All')
    const [sortField, setSortField] = useState('openingRank')
    const [sortDir, setSortDir] = useState('asc')
    const [currentPage, setCurrentPage] = useState(1)
    const [selected, setSelected] = useState(null)
    const itemsPerPage = 30

    const filtered = useMemo(() => {
        let result = instituteData.filter(i => {
            if (search && !i.institute.toLowerCase().includes(search.toLowerCase())) return false
            if (stateFilter !== 'All' && i.state !== stateFilter) return false
            if (feeFilter === 'Free' && i.fee !== '-') return false
            if (feeFilter === 'Paid' && i.fee === '-') return false
            return true
        })

        result = [...result].sort((a, b) => {
            const av = a[sortField]
            const bv = b[sortField]
            if (typeof av === 'number') return sortDir === 'asc' ? av - bv : bv - av
            return sortDir === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av))
        })
        return result
    }, [search, stateFilter, feeFilter, sortField, sortDir])

    const totalPages = Math.ceil(filtered.length / itemsPerPage)
    const paginated = useMemo(() => {
        const start = (currentPage - 1) * itemsPerPage
        return filtered.slice(start, start + itemsPerPage)
    }, [filtered, currentPage])

    const handleSort = (field) => {
        if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        else { setSortField(field); setSortDir('asc') }
        setCurrentPage(1)
    }

    const SortIcon = ({ field }) => {
        if (sortField !== field) return <span style={{ opacity: 0.3 }}>↕</span>
        return <span>{sortDir === 'asc' ? '↑' : '↓'}</span>
    }

    return (
        <>
            <div className="discovery-container">
                <div className="discovery-header">
                    <div className="breadcrumb">Discover / <strong>College Finder</strong></div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {filtered.length} colleges
                    </span>
                </div>

                {/* Filters */}
                <div className="filter-panel glass-panel" style={{ padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '1rem', alignItems: 'end' }}>
                        <div className="filter-group">
                            <label>Search College</label>
                            <div style={{ position: 'relative' }}>
                                <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                <input
                                    type="text"
                                    placeholder="Type college name..."
                                    value={search}
                                    onChange={e => { setSearch(e.target.value); setCurrentPage(1) }}
                                    style={{ width: '100%', paddingLeft: '2rem', padding: '8px 12px 8px 32px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: 'white', outline: 'none', fontSize: '0.875rem', boxSizing: 'border-box' }}
                                />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>State</label>
                            <div className="select-wrapper">
                                <select value={stateFilter} onChange={e => { setStateFilter(e.target.value); setCurrentPage(1) }}>
                                    <option value="All">All States</option>
                                    {STATES.map(s => <option key={s}>{s}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Fee Type</label>
                            <div className="select-wrapper">
                                <select value={feeFilter} onChange={e => { setFeeFilter(e.target.value); setCurrentPage(1) }}>
                                    <option value="All">All</option>
                                    <option value="Free">Government (Free)</option>
                                    <option value="Paid">Paid</option>
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group" style={{ alignItems: 'flex-end' }}>
                            <button className="clear-filter" onClick={() => { setSearch(''); setStateFilter('All'); setFeeFilter('All'); setSortField('openingRank'); setSortDir('asc'); setCurrentPage(1) }}>
                                Clear Filters
                            </button>
                        </div>
                    </div>
                </div>

                {/* Table */}
                <div className="ranks-table-wrapper glass-panel">
                    <table className="ranks-table">
                        <thead>
                            <tr>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('institute')}>
                                    Institute <SortIcon field="institute" />
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('state')}>
                                    State <SortIcon field="state" />
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('courses')}>
                                    Courses <SortIcon field="courses" />
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('totalSeats')}>
                                    Seats <SortIcon field="totalSeats" />
                                </th>
                                <th>Fee (₹/yr)</th>
                                <th>Stipend (₹/yr)</th>
                                <th>Bond</th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('openingRank')}>
                                    Opening Rank <SortIcon field="openingRank" />
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSort('closingRank')}>
                                    Closing Rank <SortIcon field="closingRank" />
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {paginated.map((inst, idx) => (
                                <motion.tr
                                    key={inst.institute}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: idx * 0.01 }}
                                    style={{ cursor: 'pointer' }}
                                    onClick={() => setSelected(inst)}
                                >
                                    <td className="inst-name" style={{ maxWidth: 220 }}>{inst.institute}</td>
                                    <td style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{inst.state}</td>
                                    <td style={{ textAlign: 'center' }}>{inst.courses}</td>
                                    <td style={{ textAlign: 'center' }}>{inst.totalSeats}</td>
                                    <td style={{ color: inst.fee === '-' ? '#10b981' : 'var(--text-secondary)' }}>
                                        {inst.fee === '-' ? 'Free' : inst.fee}
                                    </td>
                                    <td>{inst.stipend}</td>
                                    <td style={{ whiteSpace: 'nowrap' }}>
                                        {inst.bondYears !== '-' ? `${inst.bondYears}yr` : '-'}
                                        {inst.bondPenalty !== '-' ? <span style={{ color: '#f43f5e', fontSize: '0.75rem', marginLeft: 4 }}>₹{inst.bondPenalty}</span> : ''}
                                    </td>
                                    <td className="rank-highlight">{inst.openingRank.toLocaleString()}</td>
                                    <td style={{ color: 'var(--text-muted)' }}>{inst.closingRank.toLocaleString()}</td>
                                </motion.tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', paddingBottom: '1rem', flexShrink: 0 }}>
                        <button
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            style={{ padding: '0.5rem 1rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--panel-bg)', cursor: currentPage === 1 ? 'not-allowed' : 'pointer', opacity: currentPage === 1 ? 0.5 : 1, color: 'var(--text-primary)' }}
                        >
                            Previous
                        </button>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                            Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
                            <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>({filtered.length} results)</span>
                        </span>
                        <button
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            style={{ padding: '0.5rem 1rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--panel-bg)', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer', opacity: currentPage === totalPages ? 0.5 : 1, color: 'var(--text-primary)' }}
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>

            {/* Detail Modal */}
            {selected && (
                <div className="modal-overlay" onClick={() => setSelected(null)}>
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="modal-content"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="modal-header">
                            <h3>{selected.institute}</h3>
                            <button className="close-btn" onClick={() => setSelected(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="detail-info" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                                <p>
                                    <strong><MapPin size={12} style={{ display: 'inline' }} /> State</strong>
                                    <span>{selected.state}</span>
                                </p>
                                <p>
                                    <strong><BookOpen size={12} style={{ display: 'inline' }} /> Courses</strong>
                                    <span>{selected.courses}</span>
                                </p>
                                <p>
                                    <strong><TrendingUp size={12} style={{ display: 'inline' }} /> Total Seats</strong>
                                    <span>{selected.totalSeats}</span>
                                </p>
                                <p>
                                    <strong>Opening Rank</strong>
                                    <span style={{ color: '#10b981' }}>{selected.openingRank.toLocaleString()}</span>
                                </p>
                                <p>
                                    <strong><IndianRupee size={12} style={{ display: 'inline' }} /> Annual Fee</strong>
                                    <span style={{ color: selected.fee === '-' ? '#10b981' : 'inherit' }}>
                                        {selected.fee === '-' ? 'Free (Govt.)' : `₹${selected.fee}`}
                                    </span>
                                </p>
                                <p>
                                    <strong>Stipend (Y1)</strong>
                                    <span>{selected.stipend !== '-' ? `₹${selected.stipend}` : '-'}</span>
                                </p>
                                <p>
                                    <strong>Bond Penalty</strong>
                                    <span style={{ color: selected.bondPenalty !== '-' ? '#f43f5e' : 'inherit' }}>
                                        {selected.bondPenalty !== '-' ? `₹${selected.bondPenalty}` : 'None'}
                                    </span>
                                </p>
                                <p>
                                    <strong>Bond Duration</strong>
                                    <span>{selected.bondYears !== '-' ? `${selected.bondYears} year(s)` : 'None'}</span>
                                </p>
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', textAlign: 'center', padding: '1rem' }}>
                                Use the <strong>Closing Ranks</strong> tab to see seat-wise allotment data for this institute.
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </>
    )
}
