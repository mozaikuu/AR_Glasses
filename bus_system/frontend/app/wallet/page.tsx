"use client";

import { FormEvent, useEffect, useState } from "react";

import {
	addWalletBalance,
	getStudents,
	getWalletBalance,
	getWalletHistory,
	payWallet,
	subscribeStudent,
} from "@/lib/api";

type StudentOption = {
	id: number;
	name: string;
};

export default function WalletPage() {
	const [students, setStudents] = useState<StudentOption[]>([]);
	const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
	const [balanceData, setBalanceData] = useState<{
		balance: number;
		subscription_status: string;
		subscription_expires_at: string | null;
	} | null>(null);
	const [history, setHistory] = useState<
		Array<{
			id: number;
			type: string;
			amount: number;
			status: string;
			description: string;
			created_at: string;
		}>
	>([]);
	const [amount, setAmount] = useState(30);
	const [months, setMonths] = useState(1);
	const [forceFail, setForceFail] = useState(false);
	const [feedback, setFeedback] = useState<string>("");

	async function loadStudents() {
		const result = await getStudents("en");
		const rows = result.data.students.map((student) => ({
			id: student.id,
			name: student.name,
		}));
		setStudents(rows);
		if (!selectedStudent && rows.length > 0) {
			setSelectedStudent(rows[0].id);
		}
	}

	async function refreshWallet(studentId: number) {
		const [balanceResult, historyResult] = await Promise.all([
			getWalletBalance(studentId, "en"),
			getWalletHistory(studentId, "en"),
		]);

		setBalanceData(balanceResult.data);
		setHistory(historyResult.data.transactions);
	}

	useEffect(() => {
		void loadStudents();
	}, []);

	useEffect(() => {
		if (!selectedStudent) {
			return;
		}
		void refreshWallet(selectedStudent);
	}, [selectedStudent]);

	async function topUp(event: FormEvent) {
		event.preventDefault();
		if (!selectedStudent) {
			return;
		}

		const result = await addWalletBalance(selectedStudent, amount, "en");
		setFeedback(result.message);
		await refreshWallet(selectedStudent);
	}

	async function payTrip(event: FormEvent) {
		event.preventDefault();
		if (!selectedStudent) {
			return;
		}

		const result = await payWallet(
			selectedStudent,
			amount,
			"trip",
			forceFail,
			"en",
		);
		setFeedback(`${result.message} (${result.data.status})`);
		await refreshWallet(selectedStudent);
	}

	async function subscribe(event: FormEvent) {
		event.preventDefault();
		if (!selectedStudent) {
			return;
		}

		const result = await subscribeStudent(selectedStudent, months, "en");
		setFeedback(`${result.message} (${result.data.status})`);
		await refreshWallet(selectedStudent);
	}

	return (
		<div className="space-y-5">
			<section className="panel rounded-3xl p-6 md:p-8">
				<p className="text-xs uppercase tracking-[0.22em] text-mint-300">
					Wallet System
				</p>
				<h2 className="mt-2 text-2xl font-semibold">
					Student Wallet + Subscription
				</h2>
				<p className="mt-3 text-sm text-slate-300">
					Simulated payment gateway with successful and failed
					transactions, trip payments, and monthly subscriptions.
				</p>
			</section>

			<section className="grid gap-5 mobile-stack md:grid-cols-[1.2fr_1fr]">
				<div className="panel rounded-3xl p-5">
					<label
						className="text-sm text-slate-300"
						htmlFor="studentSelect"
					>
						Select student
					</label>
					<select
						id="studentSelect"
						className="mt-2 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
						value={selectedStudent ?? ""}
						onChange={(event) =>
							setSelectedStudent(Number(event.target.value))
						}
					>
						{students.map((student) => (
							<option key={student.id} value={student.id}>
								#{student.id} - {student.name}
							</option>
						))}
					</select>

					<div className="mt-4 grid gap-3 md:grid-cols-2">
						<div className="rounded-2xl border border-white/10 bg-white/5 p-4">
							<p className="text-xs text-slate-400">Current Balance</p>
							<p className="mt-1 text-2xl font-semibold">
								{balanceData?.balance?.toFixed(2) ?? "--"} EGP
							</p>
						</div>
						<div className="rounded-2xl border border-white/10 bg-white/5 p-4">
							<p className="text-xs text-slate-400">Subscription</p>
							<p className="mt-1 text-2xl font-semibold capitalize">
								{balanceData?.subscription_status ?? "--"}
							</p>
							{balanceData?.subscription_expires_at ? (
								<p className="mt-1 text-xs text-slate-300">
									Valid until: {balanceData.subscription_expires_at}
								</p>
							) : null}
						</div>
					</div>

					{feedback ? (
						<p className="mt-4 rounded-xl border border-mint-300/40 bg-mint-400/10 px-3 py-2 text-sm text-mint-200">
							{feedback}
						</p>
					) : null}
				</div>

				<div className="space-y-4">
					<form className="panel rounded-3xl p-5" onSubmit={topUp}>
						<h3 className="text-lg font-medium">Add Balance</h3>
						<input
							type="number"
							className="mt-3 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
							min={1}
							step={1}
							value={amount}
							onChange={(event) => setAmount(Number(event.target.value))}
						/>
						<button
							type="submit"
							className="mt-3 rounded-xl bg-mint-500/80 px-4 py-2 text-sm font-semibold text-black transition hover:bg-mint-300"
						>
							Add Funds
						</button>
					</form>

					<form className="panel rounded-3xl p-5" onSubmit={payTrip}>
						<h3 className="text-lg font-medium">Pay Trip Fee</h3>
						<input
							type="number"
							className="mt-3 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
							min={1}
							step={1}
							value={amount}
							onChange={(event) => setAmount(Number(event.target.value))}
						/>
						<label className="mt-3 flex items-center gap-2 text-xs text-slate-300">
							<input
								type="checkbox"
								checked={forceFail}
								onChange={(event) => setForceFail(event.target.checked)}
							/>
							Simulate failed payment
						</label>
						<button
							type="submit"
							className="mt-3 rounded-xl bg-amber-500/80 px-4 py-2 text-sm font-semibold text-black transition hover:bg-amber-300"
						>
							Pay Trip
						</button>
					</form>

					<form className="panel rounded-3xl p-5" onSubmit={subscribe}>
						<h3 className="text-lg font-medium">Monthly Subscription</h3>
						<input
							type="number"
							className="mt-3 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
							min={1}
							max={12}
							value={months}
							onChange={(event) => setMonths(Number(event.target.value))}
						/>
						<button
							type="submit"
							className="mt-3 rounded-xl bg-sky-500/80 px-4 py-2 text-sm font-semibold text-black transition hover:bg-sky-300"
						>
							Subscribe
						</button>
					</form>
				</div>
			</section>

			<section className="panel rounded-3xl p-5">
				<h3 className="text-lg font-medium">Transaction History</h3>
				<div className="mt-4 overflow-x-auto">
					<table className="min-w-full text-left text-sm">
						<thead className="text-slate-400">
							<tr>
								<th className="pb-2 pr-3">Time</th>
								<th className="pb-2 pr-3">Type</th>
								<th className="pb-2 pr-3">Amount</th>
								<th className="pb-2 pr-3">Status</th>
								<th className="pb-2">Description</th>
							</tr>
						</thead>
						<tbody>
							{history.slice(0, 12).map((item) => (
								<tr key={item.id} className="border-t border-white/10">
									<td className="py-2 pr-3 text-xs text-slate-300">
										{item.created_at}
									</td>
									<td className="py-2 pr-3">{item.type}</td>
									<td className="py-2 pr-3">{item.amount}</td>
									<td className="py-2 pr-3">
										<span
											className={
												item.status === "success"
													? "rounded-full bg-mint-500/20 px-2 py-1 text-xs text-mint-200"
													: "rounded-full bg-rose-500/20 px-2 py-1 text-xs text-rose-200"
											}
										>
											{item.status}
										</span>
									</td>
									<td className="py-2 text-slate-300">
										{item.description}
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</section>
		</div>
	);
}
