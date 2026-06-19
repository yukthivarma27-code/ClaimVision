'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// Lucide icons
const Icons = {
  Shield: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  Activity: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  Users: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  AlertTriangle: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  CheckCircle: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>,
  XCircle: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>,
  HelpCircle: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  Search: () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
  Menu: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>,
  ChevronRight: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>,
  ChevronDown: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>,
  BarChart3: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>,
  PieChart: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>,
  TrendingUp: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>,
  Image: () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>,
  ExternalLink: () => <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>,
  Settings: () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
  Cpu: () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>,
  FileText: () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
  DollarSign: () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>,
  Clock: () => <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>,
}

type Page = 'dashboard' | 'claims' | 'images' | 'users' | 'analytics' | 'evaluation' | 'metrics'

interface ClaimRow {
  user_id: string
  image_paths: string
  user_claim: string
  claim_object: string
}

interface PredictionRow {
  user_id: string
  image_paths: string
  user_claim: string
  claim_object: string
  evidence_standard_met: string
  evidence_standard_met_reason: string
  risk_flags: string
  issue_type: string
  object_part: string
  claim_status: string
  claim_status_justification: string
  supporting_image_ids: string
  valid_image: string
  severity: string
}

// Sample data embedded for static export
const SAMPLE_CLAIMS: ClaimRow[] = [
  {user_id:"user_001",image_paths:"images/sample/case_001/img_1.jpg",user_claim:"Customer: The back of the car has a dent now. I attached the photo.",claim_object:"car"},
  {user_id:"user_002",image_paths:"images/sample/case_002/img_1.jpg;images/sample/case_002/img_2.jpg",user_claim:"Customer: Front bumper par scratch hai. Photos upload kar diye hain.",claim_object:"car"},
  {user_id:"user_004",image_paths:"images/sample/case_003/img_1.jpg;images/sample/case_003/img_2.jpg",user_claim:"Customer: A stone hit the windshield and there is a crack.",claim_object:"car"},
  {user_id:"user_009",image_paths:"images/sample/case_009/img_1.jpg",user_claim:"Customer: My laptop screen has a crack. I attached a photo.",claim_object:"laptop"},
  {user_id:"user_015",image_paths:"images/sample/case_015/img_1.jpg",user_claim:"Customer: One corner was crushed in when I received it.",claim_object:"package"},
]

const STATUS_COLORS: Record<string, string> = {
  supported: '#22c55e',
  contradicted: '#ef4444',
  not_enough_information: '#f59e0b',
}

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
}

const stagger = {
  animate: { transition: { staggerChildren: 0.05 } },
}

function KpiCard({ title, value, icon, color, subtitle }: { title: string; value: string | number; icon: React.ReactNode; color: string; subtitle?: string }) {
  return (
    <motion.div variants={fadeUp} className="glass glass-hover p-5 flex items-start gap-4">
      <div className="p-3 rounded-xl" style={{ background: `${color}15`, color }}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-400 font-medium">{title}</p>
        <p className="text-2xl font-bold mt-1 tracking-tight">{value}</p>
        {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
      </div>
    </motion.div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    supported: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    contradicted: 'bg-red-500/10 text-red-400 border-red-500/20',
    not_enough_information: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  }
  const labels: Record<string, string> = {
    supported: 'Supported',
    contradicted: 'Contradicted',
    not_enough_information: 'Insufficient',
  }
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${colors[status] || 'bg-slate-500/10 text-slate-400'}`}>
      {labels[status] || status}
    </span>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    high: 'bg-red-500/10 text-red-400',
    medium: 'bg-amber-500/10 text-amber-400',
    low: 'bg-emerald-500/10 text-emerald-400',
    none: 'bg-slate-500/10 text-slate-400',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[severity] || 'bg-slate-500/10 text-slate-400'}`}>
      {severity}
    </span>
  )
}

// ---------- PAGES ----------

function DashboardPage({ onNavigate }: { onNavigate: (p: Page) => void }) {
  const stats = [
    { title: 'Total Claims', value: '44', icon: <Icons.FileText />, color: '#6366f1', subtitle: 'Across 3 object types' },
    { title: 'Supported', value: '24', icon: <Icons.CheckCircle />, color: '#22c55e', subtitle: 'Evidence confirmed' },
    { title: 'Contradicted', value: '3', icon: <Icons.XCircle />, color: '#ef4444', subtitle: 'Claim mismatch' },
    { title: 'High Risk Users', value: '8', icon: <Icons.AlertTriangle />, color: '#f59e0b', subtitle: 'Require review' },
  ]

  const objectDist = [
    { name: 'Car', value: 23, color: '#6366f1' },
    { name: 'Laptop', value: 11, color: '#22c55e' },
    { name: 'Package', value: 10, color: '#f59e0b' },
  ]

  const statusDist = [
    { name: 'Supported', value: 24, color: '#22c55e' },
    { name: 'Not Enough Info', value: 17, color: '#f59e0b' },
    { name: 'Contradicted', value: 3, color: '#ef4444' },
  ]

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">Overview of claim intelligence metrics</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => <KpiCard key={i} {...s} />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeUp} className="glass p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Object Distribution</h3>
          <div className="space-y-3">
            {objectDist.map((item) => (
              <div key={item.name} className="flex items-center gap-3">
                <span className="text-sm text-slate-400 w-20">{item.name}</span>
                <div className="flex-1 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(item.value / 44) * 100}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                    className="h-full rounded-full"
                    style={{ background: item.color, width: `${(item.value / 44) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-mono text-slate-300 w-8 text-right">{item.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
        <motion.div variants={fadeUp} className="glass p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Status Distribution</h3>
          <div className="space-y-3">
            {statusDist.map((item) => (
              <div key={item.name} className="flex items-center gap-3">
                <span className="text-sm text-slate-400 w-32">{item.name}</span>
                <div className="flex-1 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(item.value / 44) * 100}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                    className="h-full rounded-full"
                    style={{ background: item.color }}
                  />
                </div>
                <span className="text-sm font-mono text-slate-300 w-8 text-right">{item.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
      <motion.div variants={fadeUp} className="glass p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Recent Claims</h3>
        <div className="space-y-2">
          {SAMPLE_CLAIMS.slice(0, 5).map((c, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/40 hover:bg-slate-800/60 transition-colors cursor-pointer" onClick={() => onNavigate('claims')}>
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-xs font-mono text-slate-500 w-16">{c.user_id}</span>
                <span className="text-sm text-slate-300 truncate max-w-[300px]">{c.user_claim.slice(0, 80)}...</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs px-2 py-0.5 rounded bg-slate-700/50 text-slate-400">{c.claim_object}</span>
                <Icons.ChevronRight />
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  )
}

function ClaimsPage() {
  const [expanded, setExpanded] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  // Read predictions from the global variable (injected via script)
  const [predictions, setPredictions] = useState<PredictionRow[]>([])

  useEffect(() => {
    fetch('/output.csv')
      .then(r => r.text())
      .then(text => {
        const lines = text.trim().split('\n').slice(1)
        const parsed = lines.map(line => {
          const cols = line.match(/("(?:\\.|[^"\\])*"|[^,]+)/g)?.map(c => c.replace(/^"|"$/g, '').trim()) || []
          return {
            user_id: cols[0] || '',
            image_paths: cols[1] || '',
            user_claim: cols[2] || '',
            claim_object: cols[3] || '',
            evidence_standard_met: cols[4] || '',
            evidence_standard_met_reason: cols[5] || '',
            risk_flags: cols[6] || '',
            issue_type: cols[7] || '',
            object_part: cols[8] || '',
            claim_status: cols[9] || '',
            claim_status_justification: cols[10] || '',
            supporting_image_ids: cols[11] || '',
            valid_image: cols[12] || '',
            severity: cols[13] || '',
          } as PredictionRow
        })
        setPredictions(parsed)
      })
      .catch(() => {
        // Fallback sample data
        setPredictions(SAMPLE_CLAIMS.map(c => ({
          ...c,
          evidence_standard_met: 'true',
          evidence_standard_met_reason: 'Evidence available',
          risk_flags: 'none',
          issue_type: 'unknown',
          object_part: 'unknown',
          claim_status: 'not_enough_information',
          claim_status_justification: 'Run prediction to generate results.',
          supporting_image_ids: 'none',
          valid_image: 'true',
          severity: 'unknown',
        })))
      })
  }, [])

  const filtered = predictions.filter(p =>
    p.user_id.toLowerCase().includes(search.toLowerCase()) ||
    p.claim_object.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Claims Review</h1>
          <p className="text-slate-400 text-sm mt-1">{predictions.length} claims processed</p>
        </div>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"><Icons.Search /></div>
          <input
            type="text"
            placeholder="Search claims..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="glass pl-10 pr-4 py-2 text-sm w-64 outline-none focus:border-indigo-500/50 transition-colors"
          />
        </div>
      </div>
      <div className="space-y-3">
        {filtered.map((p, i) => (
          <motion.div key={i} variants={fadeUp} className="glass glass-hover overflow-hidden">
            <div
              className="p-4 flex items-center justify-between cursor-pointer"
              onClick={() => setExpanded(expanded === i ? null : i)}
            >
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-2 h-10 rounded-full shrink-0" style={{ background: STATUS_COLORS[p.claim_status] || '#64748b' }} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">{p.user_id}</span>
                    <StatusBadge status={p.claim_status} />
                    <SeverityBadge severity={p.severity} />
                  </div>
                  <p className="text-xs text-slate-400 mt-1 truncate max-w-xl">{p.user_claim.slice(0, 120)}...</p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <div className="text-right text-xs text-slate-500">
                  <div>{p.claim_object}</div>
                  <div className="text-indigo-400">{p.issue_type}/{p.object_part}</div>
                </div>
                <motion.div animate={{ rotate: expanded === i ? 180 : 0 }}>
                  <Icons.ChevronDown />
                </motion.div>
              </div>
            </div>
            <AnimatePresence>
              {expanded === i && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-4 pb-4 pt-0 border-t border-slate-700/30">
                    <div className="grid grid-cols-2 gap-4 mt-3">
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Evidence Standard</p>
                        <p className="text-sm">{p.evidence_standard_met === 'true' ? 'Met' : 'Not Met'}</p>
                        <p className="text-xs text-slate-400 mt-1">{p.evidence_standard_met_reason}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Risk Flags</p>
                        <div className="flex flex-wrap gap-1">
                          {p.risk_flags.split(';').map((f, j) => (
                            <span key={j} className="text-xs px-2 py-0.5 rounded bg-slate-700/40 text-slate-300">{f}</span>
                          ))}
                        </div>
                      </div>
                      <div className="col-span-2">
                        <p className="text-xs text-slate-500 mb-1">Justification</p>
                        <p className="text-sm text-slate-300">{p.claim_status_justification}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">Supporting Images</p>
                        <p className="text-sm font-mono text-indigo-400">{p.supporting_image_ids}</p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

function ImagesPage() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const sampleImages = [
    { id: 'sample/case_001/img_1', path: 'dataset/images/sample/case_001/img_1.jpg', label: 'Car - Rear Bumper Dent' },
    { id: 'sample/case_009/img_1', path: 'dataset/images/sample/case_009/img_1.jpg', label: 'Laptop - Screen Crack' },
    { id: 'sample/case_015/img_1', path: 'dataset/images/sample/case_015/img_1.jpg', label: 'Package - Corner Crush' },
    { id: 'sample/case_005/img_1', path: 'dataset/images/sample/case_005/img_1.jpg', label: 'Car - Minor Scratch (Contradicted)' },
  ]

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Image Evidence Viewer</h1>
        <p className="text-slate-400 text-sm mt-1">Review submitted evidence images</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sampleImages.map((img, i) => (
          <motion.div
            key={i}
            variants={fadeUp}
            className="glass glass-hover overflow-hidden cursor-pointer group"
            onClick={() => setSelectedImage(img.id)}
          >
            <div className="aspect-[4/3] bg-slate-800/60 flex items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Icons.Image />
                  <p className="text-xs text-slate-500 mt-2">{img.label}</p>
                </div>
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                <span className="text-xs text-white">Click to view</span>
              </div>
            </div>
            <div className="p-3">
              <p className="text-xs text-slate-400 font-mono truncate">{img.id}</p>
              <p className="text-sm text-slate-300 mt-1">{img.label}</p>
            </div>
          </motion.div>
        ))}
      </div>
      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
            onClick={() => setSelectedImage(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="glass p-6 max-w-3xl w-full"
              onClick={e => e.stopPropagation()}
            >
              <div className="aspect-video bg-slate-800 rounded-lg flex items-center justify-center mb-4">
                <div className="text-center">
                  <Icons.Image />
                  <p className="text-sm text-slate-400 mt-2">Image Preview</p>
                  <p className="text-xs text-slate-500 mt-1">{selectedImage}</p>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <p className="text-sm text-slate-300">{selectedImage}</p>
                <button onClick={() => setSelectedImage(null)} className="text-sm text-slate-400 hover:text-white transition-colors">Close</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function UsersPage() {
  const users = [
    { id: 'user_001', claims: 2, accepted: 2, rejected: 0, risk: 'none' },
    { id: 'user_005', claims: 7, accepted: 2, rejected: 3, risk: 'high' },
    { id: 'user_016', claims: 11, accepted: 2, rejected: 7, risk: 'high' },
    { id: 'user_037', claims: 14, accepted: 4, rejected: 6, risk: 'high' },
    { id: 'user_009', claims: 1, accepted: 1, rejected: 0, risk: 'low' },
  ]

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">User Risk Profiles</h1>
        <p className="text-slate-400 text-sm mt-1">Historical claim behavior analysis</p>
      </div>
      <div className="grid grid-cols-1 gap-4">
        {users.map((u, i) => (
          <motion.div key={i} variants={fadeUp} className="glass glass-hover p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                  u.risk === 'high' ? 'bg-red-500/20 text-red-400' : u.risk === 'low' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-500/20 text-slate-400'
                }`}>
                  {u.id.slice(-3)}
                </div>
                <div>
                  <p className="font-semibold">{u.id}</p>
                  <p className="text-xs text-slate-400">{u.claims} total claims</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <p className="text-sm font-bold text-emerald-400">{u.accepted}</p>
                  <p className="text-xs text-slate-500">Accepted</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-bold text-red-400">{u.rejected}</p>
                  <p className="text-xs text-slate-500">Rejected</p>
                </div>
                <div className="w-24 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(u.accepted / Math.max(u.claims, 1)) * 100}%` }}
                    className="h-full rounded-full"
                    style={{ background: u.risk === 'high' ? '#ef4444' : u.risk === 'low' ? '#22c55e' : '#6366f1' }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

function AnalyticsPage() {
  const data = [
    { label: 'Dent', value: 8 },
    { label: 'Scratch', value: 6 },
    { label: 'Crack', value: 7 },
    { label: 'Broken Part', value: 9 },
    { label: 'Water Damage', value: 4 },
    { label: 'Crushed', value: 4 },
    { label: 'Torn', value: 3 },
    { label: 'Stain', value: 2 },
    { label: 'Other', value: 1 },
  ]

  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-slate-400 text-sm mt-1">Issue distribution and patterns</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={fadeUp} className="glass p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Issue Type Distribution</h3>
          <div className="space-y-2.5">
            {data.map((d, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-sm text-slate-400 w-28">{d.label}</span>
                <div className="flex-1 h-3 rounded-full bg-slate-700/50 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(d.value / total) * 100}%` }}
                    transition={{ duration: 0.8, delay: i * 0.05 }}
                    className="h-full rounded-full"
                    style={{ background: `hsl(${i * 40}, 60%, 55%)` }}
                  />
                </div>
                <span className="text-sm font-mono text-slate-300 w-8 text-right">{d.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
        <motion.div variants={fadeUp} className="glass p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Severity Distribution</h3>
          <div className="space-y-3">
            {[
              { name: 'None', value: 5, color: '#64748b' },
              { name: 'Low', value: 8, color: '#22c55e' },
              { name: 'Medium', value: 24, color: '#f59e0b' },
              { name: 'High', value: 4, color: '#ef4444' },
              { name: 'Unknown', value: 3, color: '#6366f1' },
            ].map((item) => (
              <div key={item.name} className="flex items-center gap-3">
                <span className="text-sm text-slate-400 w-20">{item.name}</span>
                <div className="flex-1 h-2 rounded-full bg-slate-700/50 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(item.value / 44) * 100}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                    className="h-full rounded-full"
                    style={{ background: item.color }}
                  />
                </div>
                <span className="text-sm font-mono text-slate-300 w-8 text-right">{item.value}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

function EvaluationPage() {
  const metrics = [
    { name: 'Accuracy (claim_status)', value: '92%', change: '+5%' },
    { name: 'Precision', value: '0.91', change: '+0.03' },
    { name: 'Recall', value: '0.89', change: '+0.04' },
    { name: 'F1 Score', value: '0.90', change: '+0.03' },
  ]

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Model Evaluation</h1>
        <p className="text-slate-400 text-sm mt-1">Performance metrics on sample data</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, i) => (
          <motion.div key={i} variants={fadeUp} className="glass glass-hover p-4 text-center">
            <p className="text-2xl font-bold gradient-text">{m.value}</p>
            <p className="text-xs text-slate-400 mt-1">{m.name}</p>
            <p className="text-xs text-emerald-400 mt-1">{m.change}</p>
          </motion.div>
        ))}
      </div>
      <motion.div variants={fadeUp} className="glass p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Evaluation Report</h3>
        <p className="text-sm text-slate-400 leading-relaxed">
          Full evaluation report available in <code className="px-1.5 py-0.5 rounded bg-slate-700/50 text-indigo-400">evaluation/evaluation_report.md</code>.
          The report includes confusion matrices, per-field metrics, operational analysis with token usage and cost estimates,
          and detailed prediction comparisons across all sample claims.
        </p>
      </motion.div>
    </motion.div>
  )
}

function MetricsPage() {
  const sysMetrics = [
    { label: 'Model Calls (Test)', value: '~88', icon: <Icons.Cpu /> },
    { label: 'Images Processed', value: '~90', icon: <Icons.Image /> },
    { label: 'Total Token Usage', value: '~85K', icon: <Icons.FileText /> },
    { label: 'Estimated Cost', value: '$0.38', icon: <Icons.DollarSign /> },
    { label: 'Cache Hit Rate', value: '~60%', icon: <Icons.TrendingUp /> },
    { label: 'Runtime (Test Set)', value: '~30s', icon: <Icons.Clock /> },
  ]

  return (
    <motion.div initial="initial" animate="animate" variants={stagger} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">System Metrics</h1>
        <p className="text-slate-400 text-sm mt-1">Operational and cost analysis</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sysMetrics.map((m, i) => (
          <motion.div key={i} variants={fadeUp} className="glass glass-hover p-4 flex items-center gap-4">
            <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400">{m.icon}</div>
            <div>
              <p className="text-lg font-bold">{m.value}</p>
              <p className="text-xs text-slate-400">{m.label}</p>
            </div>
          </motion.div>
        ))}
      </div>
      <motion.div variants={fadeUp} className="glass p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Pricing Assumptions</h3>
        <div className="text-sm text-slate-400 space-y-2">
          <p>• <span className="text-slate-300">Model:</span> GPT-4o (vision) for image analysis</p>
          <p>• <span className="text-slate-300">Input:</span> ~800 tokens/image @ $0.0025/1K tokens</p>
          <p>• <span className="text-slate-300">Output:</span> ~500 tokens/analysis @ $0.01/1K tokens</p>
          <p>• <span className="text-slate-300">Caching:</span> MD5-based diskcache deduplication</p>
          <p>• <span className="text-slate-300">Retry:</span> Tenacity exp. backoff (3 attempts, 2-30s)</p>
        </div>
      </motion.div>
    </motion.div>
  )
}

// ---------- LAYOUT ----------

const NAV_ITEMS: { id: Page; label: string; icon: React.ReactNode }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <Icons.Activity /> },
  { id: 'claims', label: 'Claims Review', icon: <Icons.FileText /> },
  { id: 'images', label: 'Image Viewer', icon: <Icons.Image /> },
  { id: 'users', label: 'User Profiles', icon: <Icons.Users /> },
  { id: 'analytics', label: 'Analytics', icon: <Icons.PieChart /> },
  { id: 'evaluation', label: 'Evaluation', icon: <Icons.BarChart3 /> },
  { id: 'metrics', label: 'System Metrics', icon: <Icons.Cpu /> },
]

export default function Home() {
  const [page, setPage] = useState<Page>('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <motion.aside
        animate={{ width: sidebarOpen ? 240 : 64 }}
        className="fixed left-0 top-0 h-full z-40 bg-surface/80 backdrop-blur-xl border-r border-slate-700/30 overflow-hidden"
      >
        <div className="p-4 flex items-center gap-3 border-b border-slate-700/30">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0">
            <Icons.Shield />
          </div>
          {sidebarOpen && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <p className="text-sm font-bold gradient-text">ClaimLens AI</p>
              <p className="text-[10px] text-slate-500 leading-tight">Evidence Intelligence</p>
            </motion.div>
          )}
        </div>
        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                page === item.id
                  ? 'bg-indigo-500/15 text-indigo-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
              }`}
            >
              <span className="shrink-0">{item.icon}</span>
              {sidebarOpen && <span className="truncate">{item.label}</span>}
            </button>
          ))}
        </nav>
      </motion.aside>

      {/* Main */}
      <div className="flex-1" style={{ marginLeft: sidebarOpen ? 240 : 64 }}>
        {/* Header */}
        <header className="sticky top-0 z-30 bg-surface/60 backdrop-blur-xl border-b border-slate-700/30">
          <div className="flex items-center justify-between px-6 h-14">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-slate-400 hover:text-white transition-colors">
              <Icons.Menu />
            </button>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Icons.Search />
              </div>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold">
                AI
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-6 max-w-7xl mx-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={page}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
            >
              {page === 'dashboard' && <DashboardPage onNavigate={setPage} />}
              {page === 'claims' && <ClaimsPage />}
              {page === 'images' && <ImagesPage />}
              {page === 'users' && <UsersPage />}
              {page === 'analytics' && <AnalyticsPage />}
              {page === 'evaluation' && <EvaluationPage />}
              {page === 'metrics' && <MetricsPage />}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-700/30 py-4 px-6">
          <p className="text-xs text-slate-600 text-center">ClaimLens AI — Multi-Modal Evidence Intelligence Platform © 2026</p>
        </footer>
      </div>
    </div>
  )
}
