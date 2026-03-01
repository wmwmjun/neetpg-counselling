import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import branchData from '../data/branchStats.json'

export const branches = branchData

export default function BranchExplorer({ searchQuery }) {
    const [sortField, setSortField] = useState('openingRank')
    const [sortDir, setSortDir] = useState('asc')
    const [typeFilter, setTypeFilter] = useState('All')

    const filtered = useMemo(() => {
        let result = branches.filter(b =>
            b.course.toLowerCase().includes((searchQuery || '').toLowerCase())
        )
        if (typeFilter !== 'All') {
            result = result.filter(b => b.type === typeFilter)
        }
        result = [...result].sort((a, b) => {
            const av = a[sortField]
            const bv = b[sortField]
            if (typeof av === 'number') return sortDir === 'asc' ? av - bv : bv - av
            return sortDir === 'asc' ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av))
        })
        return result
    }, [searchQuery, sortField, sortDir, typeFilter])

    const handleSort = (field) => {
        if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
        else { setSortField(field); setSortDir('asc') }
    }

    const getTypeBadge = (type) => {
        const className = type === 'Clinical' ? 'badge-clinical' : type === 'Para-Clinical' ? 'badge-para' : 'badge-pre'
        return <span className={`badge ${className}`}>{type}</span>
    }

    const SortIcon = ({ field }) => {
        if (sortField !== field) return <span style={{ opacity: 0.3 }}>↕</span>
        return <span>{sortDir === 'asc' ? '↑' : '↓'}</span>
    }

    return (
        <div className="explorer-container">
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                {['All', 'Clinical', 'Para-Clinical', 'Pre-Clinical'].map(t => (
                    <button
                        key={t}
                        onClick={() => setTypeFilter(t)}
                        style={{
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            border: '1px solid var(--border)',
                            background: typeFilter === t ? 'var(--accent)' : 'var(--panel-bg)',
                            color: typeFilter === t ? '#fff' : 'var(--text-secondary)',
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                        }}
                    >
                        {t}
                    </button>
                ))}
                <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.8rem', alignSelf: 'center' }}>
                    {filtered.length} branches
                </span>
            </div>

            <div className="table-wrapper glass-panel" style={{ overflowX: 'auto' }}>
                <table className="explorer-table">
                    <thead>
                        <tr>
                            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('course')}>
                                Branch Name <SortIcon field="course" />
                            </th>
                            <th>Type</th>
                            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('seats')}>
                                Allotted Seats <SortIcon field="seats" />
                            </th>
                            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('institutes')}>
                                Institutes <SortIcon field="institutes" />
                            </th>
                            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('openingRank')}>
                                Opening Rank <SortIcon field="openingRank" />
                            </th>
                            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('medianRank')}>
                                Median Rank <SortIcon field="medianRank" />
                            </th>
                            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('closingRank')}>
                                Closing Rank <SortIcon field="closingRank" />
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map((branch, index) => (
                            <motion.tr
                                key={branch.course}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: Math.min(index * 0.02, 0.5) }}
                            >
                                <td style={{ fontWeight: 600 }}>{branch.course}</td>
                                <td>{getTypeBadge(branch.type)}</td>
                                <td>{branch.seats.toLocaleString()}</td>
                                <td>{branch.institutes}</td>
                                <td className="rank-highlight">{branch.openingRank.toLocaleString()}</td>
                                <td>{branch.medianRank.toLocaleString()}</td>
                                <td style={{ color: 'var(--text-muted)' }}>{branch.closingRank.toLocaleString()}</td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
