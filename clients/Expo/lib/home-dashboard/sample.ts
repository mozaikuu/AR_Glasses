import type { Assignment, FinanceItem, ScheduleItem } from "./types";

/** Seed schedule across the week so “today” always shows something when aligned. */
export const sampleSchedule: ScheduleItem[] = [
	{
		id: "sch_1",
		title: "Digital Systems",
		courseCode: "CS201",
		location: "Hall A",
		dayOfWeek: 0,
		startTime: "10:00",
		endTime: "11:30",
	},
	{
		id: "sch_2",
		title: "Microprocessors Lab",
		courseCode: "CS215",
		location: "Lab 3",
		dayOfWeek: 1,
		startTime: "09:00",
		endTime: "12:00",
	},
	{
		id: "sch_3",
		title: "Communication Systems",
		courseCode: "EE310",
		location: "Room 204",
		dayOfWeek: 2,
		startTime: "13:00",
		endTime: "14:30",
	},
	{
		id: "sch_4",
		title: "Project Workshop",
		courseCode: "GP401",
		location: "Workshop B",
		dayOfWeek: 3,
		startTime: "11:00",
		endTime: "14:00",
	},
	{
		id: "sch_5",
		title: "Embedded Systems",
		courseCode: "CS330",
		location: "Room 112",
		dayOfWeek: 4,
		startTime: "08:30",
		endTime: "10:00",
	},
	{
		id: "sch_6",
		title: "Signals & Systems",
		courseCode: "EE240",
		location: "Hall C",
		dayOfWeek: 5,
		startTime: "14:00",
		endTime: "15:30",
	},
];

function offsetISODate(daysFromToday: number): string {
	const d = new Date();
	d.setDate(d.getDate() + daysFromToday);
	const y = d.getFullYear();
	const mo = String(d.getMonth() + 1).padStart(2, "0");
	const day = String(d.getDate()).padStart(2, "0");
	return `${y}-${mo}-${day}`;
}

/** Relative due dates so samples stay relevant. */
export const sampleAssignments: Assignment[] = [
	{
		id: "asg_1",
		title: "Lab report: ALU design",
		courseCode: "CS201",
		dueDate: offsetISODate(1),
		completed: false,
	},
	{
		id: "asg_2",
		title: "Read ch.4–5, quiz prep",
		courseCode: "EE310",
		dueDate: offsetISODate(3),
		completed: false,
	},
	{
		id: "asg_3",
		title: "PCB milestone: schematic review",
		courseCode: "GP401",
		dueDate: offsetISODate(-2),
		completed: false,
	},
	{
		id: "asg_4",
		title: "Firmware blink demo",
		courseCode: "CS330",
		dueDate: offsetISODate(7),
		completed: true,
	},
];

export const sampleFinance: FinanceItem[] = [
	{
		id: "fin_1",
		title: "Spring tuition installment",
		category: "course",
		amount: 4500,
		currency: "EGP",
		paid: false,
		dueDate: offsetISODate(14),
	},
	{
		id: "fin_2",
		title: "Lab fees",
		category: "course",
		amount: 800,
		currency: "EGP",
		paid: true,
	},
	{
		id: "fin_3",
		title: "Monthly bus pass",
		category: "bus",
		amount: 350,
		currency: "EGP",
		paid: false,
		dueDate: offsetISODate(5),
	},
	{
		id: "fin_4",
		title: "Campus shuttle card top-up",
		category: "bus",
		amount: 150,
		currency: "EGP",
		paid: true,
	},
];
