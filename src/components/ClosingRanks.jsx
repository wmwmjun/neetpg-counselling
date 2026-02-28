import { useState, useMemo, useEffect } from 'react'

import { createPortal } from 'react-dom'

import { Search, Filter, ChevronDown, Download, HelpCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import './ClosingRanks.css'
import closingRanksData from '../data/closingRanks.json'

const mockClosingRanks = closingRanksData;

export default function ClosingRanks() {
    const [filters, setFilters] = useState({
        rankFrom: '',
        rankTo: '',
        feeFrom: '',
        feeTo: '',
        stipendFrom: '',
        stipendTo: '',
        bondPenaltyFrom: '',
        bondPenaltyTo: '',
        bondYears: 'Select...',
        quota: 'Select...',
        category: 'Select...',
        institute: 'Select...',
        state: 'Select...',
        course: 'Select...',
    })

    const [selectedDetail, setSelectedDetail] = useState(null)
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 50;

    const filteredData = useMemo(() => {
        if (!mockClosingRanks) return [];
        return mockClosingRanks.filter(item => {
            // Get the last available rank across all rounds to use for range filtering
            const allRanks = [
                ...(item.ranks?.['2025_R1'] || []),
                ...(item.ranks?.['2025_R2'] || []),
                ...(item.ranks?.['2025_R3'] || [])
            ];
            const lastRank = allRanks.length > 0 ? allRanks[allRanks.length - 1] : 0;

            if (filters.rankFrom && lastRank < parseInt(filters.rankFrom)) return false
            if (filters.rankTo && lastRank > parseInt(filters.rankTo)) return false

            const feeVal = parseInt((item.fee || '0').replace(/[₹,]/g, ''))
            if (filters.feeFrom && feeVal < parseInt(filters.feeFrom)) return false
            if (filters.feeTo && feeVal > parseInt(filters.feeTo)) return false

            const stipendVal = parseInt((item.stipend || '0').replace(/[₹,]/g, ''))
            if (filters.stipendFrom && stipendVal < parseInt(filters.stipendFrom)) return false
            if (filters.stipendTo && stipendVal > parseInt(filters.stipendTo)) return false

            if (filters.quota !== 'Select...' && item.quota !== filters.quota) return false
            if (filters.category !== 'Select...' && item.category !== filters.category) return false
            if (filters.state !== 'Select...' && item.state !== filters.state) return false
            if (filters.bondYears !== 'Select...' && String(item.bondYears) !== filters.bondYears.split(' ')[0]) return false
            if (filters.course !== 'Select...' && item.course !== filters.course) return false

            return true
        })
    }, [filters])


    useEffect(() => {
        setCurrentPage(1);
    }, [filters]);


    const paginatedData = useMemo(() => {
        const startIdx = (currentPage - 1) * itemsPerPage;
        return filteredData.slice(startIdx, startIdx + itemsPerPage);
    }, [filteredData, currentPage]);

    const totalPages = Math.ceil(filteredData.length / itemsPerPage);

    const filterOptions = useMemo(() => {
        const options = {
            quotas: new Set(),
            categories: new Set(),
            states: new Set(),
            courses: new Set()
        };

        mockClosingRanks.forEach(item => {
            if (item.quota) options.quotas.add(item.quota);
            if (item.category) options.categories.add(item.category);
            if (item.state) options.states.add(item.state);
            if (item.course) options.courses.add(item.course);
        });

        return {
            quotas: Array.from(options.quotas).sort(),
            categories: Array.from(options.categories).sort(),
            states: Array.from(options.states).sort(),
            courses: Array.from(options.courses).sort()
        };
    }, []);

    const handleInputChange = (field, value) => {
        setFilters(prev => ({ ...prev, [field]: value }))
    }

    const renderRankCell = (item, round) => {
        const ranks = item.ranks?.[round]
        if (!ranks || ranks.length === 0) return '-'

        const closingRank = ranks[ranks.length - 1]
        const count = ranks.length

        return (
            <div
                className="rank-cell-content"
                onClick={() => {
                    setSelectedDetail({ item, round, ranks });
                }}

                style={{ cursor: 'pointer' }}
            >

                <span className="closing-rank">{closingRank}</span>
                <span className="seat-count">({count})</span>
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

                <div className="filter-panel glass-panel">
                    <div className="filter-grid">
                        <div className="filter-group">
                            <label>Closing Rank</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="1" value={filters.rankFrom} onChange={(e) => handleInputChange('rankFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="230087" value={filters.rankTo} onChange={(e) => handleInputChange('rankTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Fee (₹)</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="0" value={filters.feeFrom} onChange={(e) => handleInputChange('feeFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="22950000" value={filters.feeTo} onChange={(e) => handleInputChange('feeTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Stipend (₹)</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="0" value={filters.stipendFrom} onChange={(e) => handleInputChange('stipendFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="1560000" value={filters.stipendTo} onChange={(e) => handleInputChange('stipendTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Bond Penalty (₹)</label>
                            <div className="range-inputs">
                                <span>From</span>
                                <input type="number" placeholder="0" value={filters.bondPenaltyFrom} onChange={(e) => handleInputChange('bondPenaltyFrom', e.target.value)} />
                                <span>To</span>
                                <input type="number" placeholder="25000000" value={filters.bondPenaltyTo} onChange={(e) => handleInputChange('bondPenaltyTo', e.target.value)} />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Bond Years</label>
                            <div className="select-wrapper">
                                <select value={filters.bondYears} onChange={(e) => handleInputChange('bondYears', e.target.value)}>
                                    <option>Select...</option>
                                    <option>0 Year</option>
                                    <option>1 Year</option>
                                    <option>2 Years</option>
                                    <option>3 Years</option>
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Quota</label>
                            <div className="select-wrapper">
                                <select value={filters.quota} onChange={(e) => handleInputChange('quota', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.quotas.map(q => <option key={q}>{q}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>Category</label>
                            <div className="select-wrapper">
                                <select value={filters.category} onChange={(e) => handleInputChange('category', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.categories.map(c => <option key={c}>{c}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group">
                            <label>State</label>
                            <div className="select-wrapper">
                                <select value={filters.state} onChange={(e) => handleInputChange('state', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.states.map(s => <option key={s}>{s}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>

                        <div className="filter-group" style={{ justifyContent: 'flex-end', paddingTop: '1.5rem' }}>
                            <button className="clear-filter" onClick={() => setFilters({
                                rankFrom: '', rankTo: '', feeFrom: '', feeTo: '', stipendFrom: '', stipendTo: '',
                                bondPenaltyFrom: '', bondPenaltyTo: '', bondYears: 'Select...',
                                quota: 'Select...', category: 'Select...',
                                institute: 'Select...', state: 'Select...', course: 'Select...'
                            })}>
                                <Download size={16} /> Clear Filters
                            </button>
                        </div>

                        <div className="filter-group full-width">
                            <label>Course</label>
                            <div className="select-wrapper">
                                <select value={filters.course} onChange={(e) => handleInputChange('course', e.target.value)}>
                                    <option>Select...</option>
                                    {filterOptions.courses.map(c => <option key={c}>{c}</option>)}
                                </select>
                                <ChevronDown size={14} className="select-icon" />
                            </div>
                        </div>
                    </div>


                </div>

                <div className="data-info">
                    <span>Showing <strong>{(currentPage - 1) * itemsPerPage + 1} - {Math.min(currentPage * itemsPerPage, filteredData.length)}</strong> of <strong>{filteredData.length}</strong> matches. (Total Records: {mockClosingRanks.length})</span>
                    <button className="sort-btn">Sort Data</button>
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
                                <th>Fee</th>
                                <th>Stipend</th>
                                <th>Bond Penalty</th>
                                <th>Bond Years</th>
                                <th>2025 R1</th>
                                <th>2025 R2</th>
                                <th>2025 R3</th>
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
                                    <td className="rank-highlight">{renderRankCell(item, '2025_R1')}</td>
                                    <td className="rank-highlight">{renderRankCell(item, '2025_R2')}</td>
                                    <td className="rank-highlight">{renderRankCell(item, '2025_R3')}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {totalPages > 1 && (
                    <div className="pagination-controls" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1.5rem', paddingBottom: '2rem', flexShrink: 0 }}>
                        <button
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            style={{ padding: '0.5rem 1rem', borderRadius: '0.5rem', border: '1px solid var(--border)', background: 'var(--panel-bg)', cursor: currentPage === 1 ? 'not-allowed' : 'pointer', opacity: currentPage === 1 ? 0.5 : 1, color: 'var(--text-primary)' }}
                        >
                            Previous
                        </button>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                            Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
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
                                    <p><strong>Institute</strong> <span>{selectedDetail.item.institute}</span></p>
                                    <p><strong>Course</strong> <span>{selectedDetail.item.course}</span></p>
                                    <p><strong>Round</strong> <span>{selectedDetail.round}</span></p>
                                    <p><strong>Total Allotments</strong> <span>{selectedDetail.ranks.length}</span></p>
                                </div>
                                <table className="allotment-list-table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>S.No</th>
                                            <th>State</th>
                                            <th>Institute</th>
                                            <th>Course</th>
                                            <th>Quota</th>
                                            <th>Category</th>
                                            <th>AI Rank</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {selectedDetail.ranks.map((rank, index) => (
                                            <tr key={index}>
                                                <td>{index + 1}</td>
                                                <td>-</td>
                                                <td>{selectedDetail.item.state}</td>
                                                <td>{selectedDetail.item.institute}</td>
                                                <td>{selectedDetail.item.course}</td>
                                                <td>{selectedDetail.item.quota}</td>
                                                <td>{selectedDetail.item.category}</td>
                                                <td className="rank-highlight">{rank}</td>
                                            </tr>
                                        ))}
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

