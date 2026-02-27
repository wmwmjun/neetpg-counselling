import { motion } from 'framer-motion'

export const branches = [
    { id: 1, name: 'Radio Diagnosis', type: 'Clinical', seats: 1240, cutoff: 1540, trend: '+12%' },
    { id: 2, name: 'General Medicine', type: 'Clinical', seats: 3420, cutoff: 3200, trend: '+5%' },
    { id: 3, name: 'Dermatology', type: 'Clinical', seats: 850, cutoff: 2100, trend: '+8%' },
    { id: 4, name: 'Pediatrics', type: 'Clinical', seats: 2100, cutoff: 5800, trend: '-2%' },
    { id: 5, name: 'General Surgery', type: 'Clinical', seats: 2800, cutoff: 8500, trend: '+1%' },
    { id: 6, name: 'Pathology', type: 'Para-Clinical', seats: 1500, cutoff: 18000, trend: '+4%' },
    { id: 7, name: 'Pharmacology', type: 'Para-Clinical', seats: 900, cutoff: 35000, trend: '-10%' },
    { id: 8, name: 'Anatomy', type: 'Pre-Clinical', seats: 600, cutoff: 55000, trend: '-15%' },
]

export default function BranchExplorer({ searchQuery }) {
    const filteredBranches = branches.filter(b =>
        b.name.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const getTypeBadge = (type) => {
        const className = type === 'Clinical' ? 'badge-clinical' : type === 'Para-Clinical' ? 'badge-para' : 'badge-pre'
        return <span className={`badge ${className}`}>{type}</span>
    }

    return (
        <div className="explorer-container">
            <div className="table-wrapper glass-panel">
                <table className="explorer-table">
                    <thead>
                        <tr>
                            <th>Branch Name</th>
                            <th>Type</th>
                            <th>Total Seats</th>
                            <th>Avg. Cut-off Rank</th>
                            <th>Popularity Trend</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredBranches.map((branch, index) => (
                            <motion.tr
                                key={branch.id}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <td style={{ fontWeight: 600 }}>{branch.name}</td>
                                <td>{getTypeBadge(branch.type)}</td>
                                <td>{branch.seats.toLocaleString()}</td>
                                <td>{branch.cutoff.toLocaleString()}</td>
                                <td style={{ color: branch.trend.startsWith('+') ? '#10b981' : '#f43f5e' }}>
                                    {branch.trend}
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
