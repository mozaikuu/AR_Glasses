import "@/global.css";
import { Ionicons } from "@expo/vector-icons";
import { useCallback, useMemo, useState } from "react";
import {
	Alert,
	KeyboardAvoidingView,
	Modal,
	Platform,
	Pressable,
	ScrollView,
	StyleSheet,
	Switch,
	Text,
	TextInput,
	View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import type { Assignment, FinanceCategory, FinanceItem, ScheduleItem, WeekdayIndex } from "@/lib/home-dashboard";
import {
	financeTotals,
	newId,
	overdueAssignments,
	pendingAssignments,
	sampleAssignments,
	sampleFinance,
	sampleSchedule,
	scheduleForDay,
	toLocalISODateString,
} from "@/lib/home-dashboard";

const WEEKDAY_LABELS: readonly string[] = [
	"Sun",
	"Mon",
	"Tue",
	"Wed",
	"Thu",
	"Fri",
	"Sat",
];

function formatMoney(amount: number, currency: string): string {
	return `${amount.toLocaleString()} ${currency}`;
}

export default function HomeDashboard() {
	const insets = useSafeAreaInsets();
	const today = useMemo(() => new Date(), []);

	const [schedule, setSchedule] = useState<ScheduleItem[]>(sampleSchedule);
	const [assignments, setAssignments] = useState<Assignment[]>(
		sampleAssignments,
	);
	const [finance, setFinance] = useState<FinanceItem[]>(sampleFinance);

	const todaySchedule = useMemo(
		() => scheduleForDay(schedule, today),
		[schedule, today],
	);
	const pending = useMemo(
		() => pendingAssignments(assignments),
		[assignments],
	);
	const overdue = useMemo(
		() => overdueAssignments(assignments, today),
		[assignments, today],
	);
	const totals = useMemo(() => financeTotals(finance), [finance]);

	const summary = useMemo(
		() => ({
			todayCount: todaySchedule.length,
			pendingCount: pending.length,
			overdueCount: overdue.length,
			courseUnpaid: totals.courseUnpaid,
			busUnpaid: totals.busUnpaid,
			currency: totals.currency,
		}),
		[todaySchedule.length, pending.length, overdue.length, totals],
	);

	/* —— Schedule modal —— */
	const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
	const [scheduleEditingId, setScheduleEditingId] = useState<string | null>(
		null,
	);
	const [schTitle, setSchTitle] = useState("");
	const [schCode, setSchCode] = useState("");
	const [schLocation, setSchLocation] = useState("");
	const [schDay, setSchDay] = useState<WeekdayIndex>(0);
	const [schStart, setSchStart] = useState("09:00");
	const [schEnd, setSchEnd] = useState("10:00");

	const openAddSchedule = useCallback(() => {
		setScheduleEditingId(null);
		setSchTitle("");
		setSchCode("");
		setSchLocation("");
		setSchDay(today.getDay() as WeekdayIndex);
		setSchStart("09:00");
		setSchEnd("10:00");
		setScheduleModalOpen(true);
	}, [today]);

	const openEditSchedule = useCallback((item: ScheduleItem) => {
		setScheduleEditingId(item.id);
		setSchTitle(item.title);
		setSchCode(item.courseCode ?? "");
		setSchLocation(item.location ?? "");
		setSchDay(item.dayOfWeek);
		setSchStart(item.startTime);
		setSchEnd(item.endTime);
		setScheduleModalOpen(true);
	}, []);

	const saveSchedule = useCallback(() => {
		const title = schTitle.trim();
		if (!title) {
			Alert.alert("Missing title", "Please enter a class title.");
			return;
		}
		if (scheduleEditingId) {
			setSchedule((prev) =>
				prev.map((s) =>
					s.id === scheduleEditingId
						? {
								...s,
								title,
								courseCode: schCode.trim() || undefined,
								location: schLocation.trim() || undefined,
								dayOfWeek: schDay,
								startTime: schStart.trim(),
								endTime: schEnd.trim(),
							}
						: s,
				),
			);
		} else {
			const row: ScheduleItem = {
				id: newId("sch"),
				title,
				courseCode: schCode.trim() || undefined,
				location: schLocation.trim() || undefined,
				dayOfWeek: schDay,
				startTime: schStart.trim(),
				endTime: schEnd.trim(),
			};
			setSchedule((prev) => [...prev, row]);
		}
		setScheduleModalOpen(false);
	}, [
		schTitle,
		schCode,
		schLocation,
		schDay,
		schStart,
		schEnd,
		scheduleEditingId,
	]);

	const deleteSchedule = useCallback(() => {
		if (!scheduleEditingId) {
			return;
		}
		Alert.alert("Delete slot?", "This removes the schedule entry.", [
			{ text: "Cancel", style: "cancel" },
			{
				text: "Delete",
				style: "destructive",
				onPress: () => {
					setSchedule((prev) => prev.filter((s) => s.id !== scheduleEditingId));
					setScheduleModalOpen(false);
				},
			},
		]);
	}, [scheduleEditingId]);

	/* —— Assignment modal —— */
	const [asgModalOpen, setAsgModalOpen] = useState(false);
	const [asgEditingId, setAsgEditingId] = useState<string | null>(null);
	const [asgTitle, setAsgTitle] = useState("");
	const [asgCode, setAsgCode] = useState("");
	const [asgDue, setAsgDue] = useState(toLocalISODateString(today));
	const [asgDone, setAsgDone] = useState(false);

	const openAddAssignment = useCallback(() => {
		setAsgEditingId(null);
		setAsgTitle("");
		setAsgCode("");
		setAsgDue(toLocalISODateString(today));
		setAsgDone(false);
		setAsgModalOpen(true);
	}, [today]);

	const openEditAssignment = useCallback((a: Assignment) => {
		setAsgEditingId(a.id);
		setAsgTitle(a.title);
		setAsgCode(a.courseCode ?? "");
		setAsgDue(a.dueDate);
		setAsgDone(a.completed);
		setAsgModalOpen(true);
	}, []);

	const saveAssignment = useCallback(() => {
		const title = asgTitle.trim();
		if (!title) {
			Alert.alert("Missing title", "Please enter an assignment title.");
			return;
		}
		if (!/^\d{4}-\d{2}-\d{2}$/.test(asgDue.trim())) {
			Alert.alert(
				"Invalid date",
				"Use YYYY-MM-DD for the due date (e.g. 2026-05-15).",
			);
			return;
		}
		if (asgEditingId) {
			setAssignments((prev) =>
				prev.map((a) =>
					a.id === asgEditingId
						? {
								...a,
								title,
								courseCode: asgCode.trim() || undefined,
								dueDate: asgDue.trim(),
								completed: asgDone,
							}
						: a,
				),
			);
		} else {
			setAssignments((prev) => [
				...prev,
				{
					id: newId("asg"),
					title,
					courseCode: asgCode.trim() || undefined,
					dueDate: asgDue.trim(),
					completed: asgDone,
				},
			]);
		}
		setAsgModalOpen(false);
	}, [asgTitle, asgCode, asgDue, asgDone, asgEditingId]);

	const deleteAssignment = useCallback(() => {
		if (!asgEditingId) {
			return;
		}
		Alert.alert("Delete assignment?", undefined, [
			{ text: "Cancel", style: "cancel" },
			{
				text: "Delete",
				style: "destructive",
				onPress: () => {
					setAssignments((prev) => prev.filter((a) => a.id !== asgEditingId));
					setAsgModalOpen(false);
				},
			},
		]);
	}, [asgEditingId]);

	const toggleAssignmentDone = useCallback((id: string) => {
		setAssignments((prev) =>
			prev.map((a) => (a.id === id ? { ...a, completed: !a.completed } : a)),
		);
	}, []);

	/* —— Finance modal —— */
	const [finModalOpen, setFinModalOpen] = useState(false);
	const [finEditingId, setFinEditingId] = useState<string | null>(null);
	const [finTitle, setFinTitle] = useState("");
	const [finCategory, setFinCategory] = useState<FinanceCategory>("course");
	const [finAmount, setFinAmount] = useState("");
	const [finCurrency, setFinCurrency] = useState("EGP");
	const [finPaid, setFinPaid] = useState(false);
	const [finDue, setFinDue] = useState("");

	const openAddFinance = useCallback((cat: FinanceCategory) => {
		setFinEditingId(null);
		setFinTitle("");
		setFinCategory(cat);
		setFinAmount("");
		setFinCurrency("EGP");
		setFinPaid(false);
		setFinDue("");
		setFinModalOpen(true);
	}, []);

	const openEditFinance = useCallback((f: FinanceItem) => {
		setFinEditingId(f.id);
		setFinTitle(f.title);
		setFinCategory(f.category);
		setFinAmount(String(f.amount));
		setFinCurrency(f.currency);
		setFinPaid(f.paid);
		setFinDue(f.dueDate ?? "");
		setFinModalOpen(true);
	}, []);

	const saveFinance = useCallback(() => {
		const title = finTitle.trim();
		if (!title) {
			Alert.alert("Missing title", "Please enter a payment title.");
			return;
		}
		const amt = Number.parseFloat(finAmount.replace(",", "."));
		if (Number.isNaN(amt) || amt < 0) {
			Alert.alert("Invalid amount", "Enter a valid number for the amount.");
			return;
		}
		const cur = finCurrency.trim() || "EGP";
		const due = finDue.trim();
		if (due && !/^\d{4}-\d{2}-\d{2}$/.test(due)) {
			Alert.alert("Invalid due date", "Use YYYY-MM-DD or leave empty.");
			return;
		}
		if (finEditingId) {
			setFinance((prev) =>
				prev.map((f) =>
					f.id === finEditingId
						? {
								...f,
								title,
								category: finCategory,
								amount: amt,
								currency: cur,
								paid: finPaid,
								dueDate: due || undefined,
							}
						: f,
				),
			);
		} else {
			setFinance((prev) => [
				...prev,
				{
					id: newId("fin"),
					title,
					category: finCategory,
					amount: amt,
					currency: cur,
					paid: finPaid,
					dueDate: due || undefined,
				},
			]);
		}
		setFinModalOpen(false);
	}, [
		finTitle,
		finCategory,
		finAmount,
		finCurrency,
		finPaid,
		finDue,
		finEditingId,
	]);

	const deleteFinance = useCallback(() => {
		if (!finEditingId) {
			return;
		}
		Alert.alert("Delete payment?", undefined, [
			{ text: "Cancel", style: "cancel" },
			{
				text: "Delete",
				style: "destructive",
				onPress: () => {
					setFinance((prev) => prev.filter((f) => f.id !== finEditingId));
					setFinModalOpen(false);
				},
			},
		]);
	}, [finEditingId]);

	const toggleFinancePaid = useCallback((id: string) => {
		setFinance((prev) =>
			prev.map((f) => (f.id === id ? { ...f, paid: !f.paid } : f)),
		);
	}, []);

	const dateLabel = useMemo(() => {
		return today.toLocaleDateString(undefined, {
			weekday: "long",
			month: "short",
			day: "numeric",
		});
	}, [today]);

	return (
		<View style={[styles.root, { paddingTop: insets.top + 8 }]}>
			<ScrollView
				contentContainerStyle={styles.scrollContent}
				keyboardShouldPersistTaps="handled"
				showsVerticalScrollIndicator={false}
			>
				<View style={styles.headerRow}>
					<View>
						<Text style={styles.title}>Home</Text>
						<Text style={styles.sub}>{dateLabel}</Text>
					</View>
					<View style={styles.headerBadge}>
						<Ionicons name="school" size={22} color="#007AFF" />
					</View>
				</View>

				<View style={styles.summaryGrid}>
					<View style={[styles.summaryCard, styles.summaryCardWide]}>
						<Text style={styles.summaryLabel}>{"Today's classes"}</Text>
						<Text style={styles.summaryValue}>{summary.todayCount}</Text>
					</View>
					<View style={styles.summaryCard}>
						<Text style={styles.summaryLabel}>Pending</Text>
						<Text style={styles.summaryValue}>{summary.pendingCount}</Text>
					</View>
					<View style={styles.summaryCard}>
						<Text style={styles.summaryLabel}>Overdue</Text>
						<Text
							style={[
								styles.summaryValue,
								summary.overdueCount > 0 && styles.summaryWarn,
							]}
						>
							{summary.overdueCount}
						</Text>
					</View>
					<View style={styles.summaryCard}>
						<Text style={styles.summaryLabel}>Course due</Text>
						<Text style={styles.summarySmall} numberOfLines={1}>
							{formatMoney(summary.courseUnpaid, summary.currency)}
						</Text>
					</View>
					<View style={styles.summaryCard}>
						<Text style={styles.summaryLabel}>Bus due</Text>
						<Text style={styles.summarySmall} numberOfLines={1}>
							{formatMoney(summary.busUnpaid, summary.currency)}
						</Text>
					</View>
				</View>

				{/* Schedule */}
				<View style={styles.sectionHeader}>
					<Text style={styles.sectionTitle}>{"Today's schedule"}</Text>
					<Pressable onPress={openAddSchedule} style={styles.addBtn}>
						<Ionicons name="add-circle-outline" size={22} color="#007AFF" />
					</Pressable>
				</View>
				{todaySchedule.length === 0 ? (
					<Text style={styles.empty}>No classes today. Add a slot or check another weekday.</Text>
				) : (
					todaySchedule.map((s) => (
						<Pressable
							key={s.id}
							onPress={() => openEditSchedule(s)}
							style={styles.listCard}
						>
							<View style={styles.listCardTop}>
								<Text style={styles.listTitle}>{s.title}</Text>
								<Text style={styles.listMeta}>
									{s.startTime} – {s.endTime}
								</Text>
							</View>
							{s.courseCode ? (
								<Text style={styles.listSub}>{s.courseCode}</Text>
							) : null}
							{s.location ? (
								<Text style={styles.listSubMuted}>
									<Ionicons name="location-outline" size={14} color="#64748b" />{" "}
									{s.location}
								</Text>
							) : null}
						</Pressable>
					))
				)}

				{/* Assignments */}
				<View style={styles.sectionHeader}>
					<Text style={styles.sectionTitle}>Assignments</Text>
					<Pressable onPress={openAddAssignment} style={styles.addBtn}>
						<Ionicons name="add-circle-outline" size={22} color="#007AFF" />
					</Pressable>
				</View>
				{assignments.map((a) => {
					const todayStr = toLocalISODateString(today);
					const overdueRow = !a.completed && a.dueDate < todayStr;
					return (
						<View key={a.id} style={styles.listCard}>
							<View style={styles.listCardTop}>
								<Pressable
									onPress={() => openEditAssignment(a)}
									style={styles.flex1}
								>
									<Text style={styles.listTitle}>{a.title}</Text>
									<Text
										style={[
											styles.listSub,
											overdueRow && styles.textOverdue,
										]}
									>
										Due {a.dueDate}
										{a.courseCode ? ` · ${a.courseCode}` : ""}
									</Text>
								</Pressable>
								<Pressable
									onPress={() => toggleAssignmentDone(a.id)}
									style={styles.iconBtn}
									hitSlop={8}
								>
									<Ionicons
										name={a.completed ? "checkmark-circle" : "ellipse-outline"}
										size={26}
										color={a.completed ? "#22c55e" : "#94a3b8"}
									/>
								</Pressable>
							</View>
						</View>
					);
				})}

				{/* Finance */}
				<View style={styles.sectionHeader}>
					<Text style={styles.sectionTitle}>Finances</Text>
				</View>
				<View style={styles.financeActions}>
					<Pressable
						style={styles.secondaryBtn}
						onPress={() => openAddFinance("course")}
					>
						<Text style={styles.secondaryBtnText}>+ Course fee</Text>
					</Pressable>
					<Pressable
						style={styles.secondaryBtn}
						onPress={() => openAddFinance("bus")}
					>
						<Text style={styles.secondaryBtnText}>+ Bus payment</Text>
					</Pressable>
				</View>
				<Text style={styles.financeTotalsLine}>
					Unpaid courses:{" "}
					<Text style={styles.bold}>
						{formatMoney(totals.courseUnpaid, totals.currency)}
					</Text>
					{" · "}
					Unpaid bus:{" "}
					<Text style={styles.bold}>
						{formatMoney(totals.busUnpaid, totals.currency)}
					</Text>
				</Text>

				<Text style={styles.financeSubheading}>Courses</Text>
				{finance.filter((f) => f.category === "course").length === 0 ? (
					<Text style={styles.empty}>No course fees yet.</Text>
				) : (
					finance
						.filter((f) => f.category === "course")
						.map((f) => (
							<View key={f.id} style={styles.listCard}>
								<View style={styles.listCardTop}>
									<Pressable
										onPress={() => openEditFinance(f)}
										style={styles.flex1}
									>
										<Text style={styles.listTitle}>{f.title}</Text>
										<Text style={styles.listSub}>
											{formatMoney(f.amount, f.currency)}
											{f.dueDate ? ` · due ${f.dueDate}` : ""}
										</Text>
									</Pressable>
									<Pressable
										onPress={() => toggleFinancePaid(f.id)}
										style={styles.paidChip}
									>
										<Text
											style={[
												styles.paidChipText,
												f.paid && styles.paidChipTextOn,
											]}
										>
											{f.paid ? "Paid" : "Unpaid"}
										</Text>
									</Pressable>
								</View>
							</View>
						))
				)}

				<Text style={styles.financeSubheading}>Bus</Text>
				{finance.filter((f) => f.category === "bus").length === 0 ? (
					<Text style={styles.empty}>No bus payments yet.</Text>
				) : (
					finance
						.filter((f) => f.category === "bus")
						.map((f) => (
							<View key={f.id} style={styles.listCard}>
								<View style={styles.listCardTop}>
									<Pressable
										onPress={() => openEditFinance(f)}
										style={styles.flex1}
									>
										<Text style={styles.listTitle}>{f.title}</Text>
										<Text style={styles.listSub}>
											{formatMoney(f.amount, f.currency)}
											{f.dueDate ? ` · due ${f.dueDate}` : ""}
										</Text>
									</Pressable>
									<Pressable
										onPress={() => toggleFinancePaid(f.id)}
										style={styles.paidChip}
									>
										<Text
											style={[
												styles.paidChipText,
												f.paid && styles.paidChipTextOn,
											]}
										>
											{f.paid ? "Paid" : "Unpaid"}
										</Text>
									</Pressable>
								</View>
							</View>
						))
				)}

				<View style={{ height: insets.bottom + 24 }} />
			</ScrollView>

			{/* Schedule modal */}
			<Modal
				visible={scheduleModalOpen}
				animationType="slide"
				transparent
				onRequestClose={() => setScheduleModalOpen(false)}
			>
				<KeyboardAvoidingView
					behavior={Platform.OS === "ios" ? "padding" : undefined}
					style={styles.modalBackdrop}
				>
					<Pressable
						style={StyleSheet.absoluteFill}
						onPress={() => setScheduleModalOpen(false)}
					/>
					<View style={[styles.modalSheet, { paddingBottom: insets.bottom + 16 }]}>
						<Text style={styles.modalTitle}>
							{scheduleEditingId ? "Edit class" : "Add class"}
						</Text>
						<Text style={styles.label}>Title</Text>
						<TextInput
							value={schTitle}
							onChangeText={setSchTitle}
							placeholder="e.g. Digital Systems"
							style={styles.input}
						/>
						<Text style={styles.label}>Course code (optional)</Text>
						<TextInput
							value={schCode}
							onChangeText={setSchCode}
							placeholder="CS201"
							style={styles.input}
						/>
						<Text style={styles.label}>Location (optional)</Text>
						<TextInput
							value={schLocation}
							onChangeText={setSchLocation}
							placeholder="Hall A"
							style={styles.input}
						/>
						<Text style={styles.label}>Day</Text>
						<View style={styles.dayRow}>
							{WEEKDAY_LABELS.map((label, i) => (
								<Pressable
									key={label}
									onPress={() => setSchDay(i as WeekdayIndex)}
									style={[
										styles.dayChip,
										schDay === i && styles.dayChipOn,
									]}
								>
									<Text
										style={[
											styles.dayChipText,
											schDay === i && styles.dayChipTextOn,
										]}
									>
										{label}
									</Text>
								</Pressable>
							))}
						</View>
						<Text style={styles.label}>Start / End (HH:MM)</Text>
						<View style={styles.row2}>
							<TextInput
								value={schStart}
								onChangeText={setSchStart}
								placeholder="09:00"
								style={[styles.input, styles.inputHalf]}
							/>
							<TextInput
								value={schEnd}
								onChangeText={setSchEnd}
								placeholder="10:30"
								style={[styles.input, styles.inputHalf]}
							/>
						</View>
						<View style={styles.modalActions}>
							{scheduleEditingId ? (
								<Pressable onPress={deleteSchedule} style={styles.dangerBtn}>
									<Text style={styles.dangerBtnText}>Delete</Text>
								</Pressable>
							) : (
								<View style={styles.flex1} />
							)}
							<Pressable
								onPress={() => setScheduleModalOpen(false)}
								style={styles.ghostBtn}
							>
								<Text style={styles.ghostBtnText}>Cancel</Text>
							</Pressable>
							<Pressable onPress={saveSchedule} style={styles.primaryBtn}>
								<Text style={styles.primaryBtnText}>Save</Text>
							</Pressable>
						</View>
					</View>
				</KeyboardAvoidingView>
			</Modal>

			{/* Assignment modal */}
			<Modal
				visible={asgModalOpen}
				animationType="slide"
				transparent
				onRequestClose={() => setAsgModalOpen(false)}
			>
				<KeyboardAvoidingView
					behavior={Platform.OS === "ios" ? "padding" : undefined}
					style={styles.modalBackdrop}
				>
					<Pressable
						style={StyleSheet.absoluteFill}
						onPress={() => setAsgModalOpen(false)}
					/>
					<View style={[styles.modalSheet, { paddingBottom: insets.bottom + 16 }]}>
						<Text style={styles.modalTitle}>
							{asgEditingId ? "Edit assignment" : "New assignment"}
						</Text>
						<Text style={styles.label}>Title</Text>
						<TextInput
							value={asgTitle}
							onChangeText={setAsgTitle}
							placeholder="Lab report"
							style={styles.input}
						/>
						<Text style={styles.label}>Course code (optional)</Text>
						<TextInput
							value={asgCode}
							onChangeText={setAsgCode}
							placeholder="CS201"
							style={styles.input}
						/>
						<Text style={styles.label}>Due date (YYYY-MM-DD)</Text>
						<TextInput
							value={asgDue}
							onChangeText={setAsgDue}
							placeholder="2026-05-15"
							style={styles.input}
						/>
						<View style={styles.switchRow}>
							<Text style={styles.label}>Completed</Text>
							<Switch value={asgDone} onValueChange={setAsgDone} />
						</View>
						<View style={styles.modalActions}>
							{asgEditingId ? (
								<Pressable onPress={deleteAssignment} style={styles.dangerBtn}>
									<Text style={styles.dangerBtnText}>Delete</Text>
								</Pressable>
							) : (
								<View style={styles.flex1} />
							)}
							<Pressable
								onPress={() => setAsgModalOpen(false)}
								style={styles.ghostBtn}
							>
								<Text style={styles.ghostBtnText}>Cancel</Text>
							</Pressable>
							<Pressable onPress={saveAssignment} style={styles.primaryBtn}>
								<Text style={styles.primaryBtnText}>Save</Text>
							</Pressable>
						</View>
					</View>
				</KeyboardAvoidingView>
			</Modal>

			{/* Finance modal */}
			<Modal
				visible={finModalOpen}
				animationType="slide"
				transparent
				onRequestClose={() => setFinModalOpen(false)}
			>
				<KeyboardAvoidingView
					behavior={Platform.OS === "ios" ? "padding" : undefined}
					style={styles.modalBackdrop}
				>
					<Pressable
						style={StyleSheet.absoluteFill}
						onPress={() => setFinModalOpen(false)}
					/>
					<View style={[styles.modalSheet, { paddingBottom: insets.bottom + 16 }]}>
						<Text style={styles.modalTitle}>
							{finEditingId ? "Edit payment" : "New payment"}
						</Text>
						<Text style={styles.label}>Title</Text>
						<TextInput
							value={finTitle}
							onChangeText={setFinTitle}
							placeholder="Tuition installment"
							style={styles.input}
						/>
						<Text style={styles.label}>Category</Text>
						<View style={styles.row2}>
							<Pressable
								onPress={() => setFinCategory("course")}
								style={[
									styles.catBtn,
									finCategory === "course" && styles.catBtnOn,
								]}
							>
								<Text
									style={[
										styles.catBtnText,
										finCategory === "course" && styles.catBtnTextOn,
									]}
								>
									Course
								</Text>
							</Pressable>
							<Pressable
								onPress={() => setFinCategory("bus")}
								style={[
									styles.catBtn,
									finCategory === "bus" && styles.catBtnOn,
								]}
							>
								<Text
									style={[
										styles.catBtnText,
										finCategory === "bus" && styles.catBtnTextOn,
									]}
								>
									Bus
								</Text>
							</Pressable>
						</View>
						<Text style={styles.label}>Amount</Text>
						<TextInput
							value={finAmount}
							onChangeText={setFinAmount}
							keyboardType="decimal-pad"
							placeholder="4500"
							style={styles.input}
						/>
						<Text style={styles.label}>Currency</Text>
						<TextInput
							value={finCurrency}
							onChangeText={setFinCurrency}
							placeholder="EGP"
							style={styles.input}
						/>
						<Text style={styles.label}>Due date (optional, YYYY-MM-DD)</Text>
						<TextInput
							value={finDue}
							onChangeText={setFinDue}
							placeholder="Leave empty if none"
							style={styles.input}
						/>
						<View style={styles.switchRow}>
							<Text style={styles.label}>Paid</Text>
							<Switch value={finPaid} onValueChange={setFinPaid} />
						</View>
						<View style={styles.modalActions}>
							{finEditingId ? (
								<Pressable onPress={deleteFinance} style={styles.dangerBtn}>
									<Text style={styles.dangerBtnText}>Delete</Text>
								</Pressable>
							) : (
								<View style={styles.flex1} />
							)}
							<Pressable
								onPress={() => setFinModalOpen(false)}
								style={styles.ghostBtn}
							>
								<Text style={styles.ghostBtnText}>Cancel</Text>
							</Pressable>
							<Pressable onPress={saveFinance} style={styles.primaryBtn}>
								<Text style={styles.primaryBtnText}>Save</Text>
							</Pressable>
						</View>
					</View>
				</KeyboardAvoidingView>
			</Modal>
		</View>
	);
}

const styles = StyleSheet.create({
	root: {
		flex: 1,
		backgroundColor: "#f8f9fa",
	},
	scrollContent: {
		paddingHorizontal: 16,
		paddingBottom: 8,
	},
	headerRow: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		marginBottom: 16,
	},
	title: {
		fontSize: 26,
		fontWeight: "800",
		color: "#0f172a",
	},
	sub: {
		marginTop: 4,
		fontSize: 14,
		color: "#64748b",
	},
	headerBadge: {
		width: 44,
		height: 44,
		borderRadius: 12,
		backgroundColor: "#e0efff",
		alignItems: "center",
		justifyContent: "center",
	},
	summaryGrid: {
		flexDirection: "row",
		flexWrap: "wrap",
		gap: 10,
		marginBottom: 20,
	},
	summaryCard: {
		backgroundColor: "#fff",
		borderRadius: 12,
		padding: 12,
		borderWidth: 1,
		borderColor: "#e5e5e5",
		width: "31%",
		minWidth: "30%",
		flexGrow: 1,
	},
	summaryCardWide: {
		width: "100%",
	},
	summaryLabel: {
		fontSize: 12,
		color: "#64748b",
		fontWeight: "600",
	},
	summaryValue: {
		marginTop: 6,
		fontSize: 22,
		fontWeight: "800",
		color: "#0f172a",
	},
	summarySmall: {
		marginTop: 6,
		fontSize: 15,
		fontWeight: "700",
		color: "#0f172a",
	},
	summaryWarn: {
		color: "#dc2626",
	},
	sectionHeader: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		marginTop: 8,
		marginBottom: 10,
	},
	sectionTitle: {
		fontSize: 18,
		fontWeight: "700",
		color: "#0f172a",
	},
	addBtn: {
		padding: 4,
	},
	empty: {
		fontSize: 14,
		color: "#64748b",
		marginBottom: 14,
		lineHeight: 20,
	},
	listCard: {
		backgroundColor: "#fff",
		borderRadius: 12,
		padding: 14,
		marginBottom: 10,
		borderWidth: 1,
		borderColor: "#e5e5e5",
	},
	listCardTop: {
		flexDirection: "row",
		alignItems: "flex-start",
		justifyContent: "space-between",
		gap: 8,
	},
	listTitle: {
		fontSize: 16,
		fontWeight: "700",
		color: "#0f172a",
	},
	listMeta: {
		fontSize: 13,
		fontWeight: "600",
		color: "#007AFF",
	},
	listSub: {
		marginTop: 4,
		fontSize: 13,
		color: "#475569",
	},
	listSubMuted: {
		marginTop: 6,
		fontSize: 13,
		color: "#64748b",
	},
	textOverdue: {
		color: "#dc2626",
		fontWeight: "600",
	},
	iconBtn: {
		paddingTop: 2,
	},
	flex1: {
		flex: 1,
	},
	financeActions: {
		flexDirection: "row",
		gap: 10,
		marginBottom: 10,
	},
	secondaryBtn: {
		flex: 1,
		paddingVertical: 10,
		borderRadius: 10,
		borderWidth: 1,
		borderColor: "#007AFF",
		alignItems: "center",
	},
	secondaryBtnText: {
		color: "#007AFF",
		fontWeight: "700",
		fontSize: 14,
	},
	financeTotalsLine: {
		fontSize: 13,
		color: "#475569",
		marginBottom: 12,
	},
	bold: {
		fontWeight: "800",
		color: "#0f172a",
	},
	financeSubheading: {
		fontSize: 14,
		fontWeight: "700",
		color: "#64748b",
		marginBottom: 8,
		marginTop: 4,
	},
	paidChip: {
		paddingHorizontal: 12,
		paddingVertical: 6,
		borderRadius: 20,
		backgroundColor: "#f1f5f9",
		alignSelf: "flex-start",
	},
	paidChipText: {
		fontSize: 13,
		fontWeight: "700",
		color: "#64748b",
	},
	paidChipTextOn: {
		color: "#16a34a",
	},
	modalBackdrop: {
		flex: 1,
		backgroundColor: "rgba(15,23,42,0.45)",
		justifyContent: "flex-end",
	},
	modalSheet: {
		backgroundColor: "#fff",
		borderTopLeftRadius: 16,
		borderTopRightRadius: 16,
		paddingHorizontal: 16,
		paddingTop: 18,
		maxHeight: "88%",
	},
	modalTitle: {
		fontSize: 18,
		fontWeight: "800",
		color: "#0f172a",
		marginBottom: 14,
	},
	label: {
		fontSize: 13,
		fontWeight: "600",
		color: "#334155",
		marginBottom: 6,
	},
	input: {
		borderWidth: 1,
		borderColor: "#e2e8f0",
		borderRadius: 10,
		paddingHorizontal: 12,
		paddingVertical: 10,
		fontSize: 15,
		color: "#0f172a",
		backgroundColor: "#fff",
		marginBottom: 12,
	},
	row2: {
		flexDirection: "row",
		gap: 10,
	},
	inputHalf: {
		flex: 1,
	},
	dayRow: {
		flexDirection: "row",
		flexWrap: "wrap",
		gap: 8,
		marginBottom: 12,
	},
	dayChip: {
		paddingHorizontal: 10,
		paddingVertical: 8,
		borderRadius: 8,
		backgroundColor: "#f1f5f9",
	},
	dayChipOn: {
		backgroundColor: "#007AFF",
	},
	dayChipText: {
		fontSize: 12,
		fontWeight: "700",
		color: "#475569",
	},
	dayChipTextOn: {
		color: "#fff",
	},
	switchRow: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		marginBottom: 8,
	},
	modalActions: {
		flexDirection: "row",
		alignItems: "center",
		gap: 8,
		marginTop: 8,
	},
	primaryBtn: {
		backgroundColor: "#007AFF",
		paddingHorizontal: 20,
		paddingVertical: 12,
		borderRadius: 10,
	},
	primaryBtnText: {
		color: "#fff",
		fontWeight: "700",
		fontSize: 15,
	},
	ghostBtn: {
		paddingHorizontal: 14,
		paddingVertical: 12,
	},
	ghostBtnText: {
		color: "#64748b",
		fontWeight: "600",
		fontSize: 15,
	},
	dangerBtn: {
		paddingHorizontal: 8,
		paddingVertical: 12,
	},
	dangerBtnText: {
		color: "#dc2626",
		fontWeight: "700",
		fontSize: 14,
	},
	catBtn: {
		flex: 1,
		paddingVertical: 12,
		borderRadius: 10,
		borderWidth: 1,
		borderColor: "#e2e8f0",
		alignItems: "center",
	},
	catBtnOn: {
		borderColor: "#007AFF",
		backgroundColor: "#e0efff",
	},
	catBtnText: {
		fontWeight: "700",
		color: "#64748b",
	},
	catBtnTextOn: {
		color: "#007AFF",
	},
});
