import {useWorkScheduleContext} from "../contexts/WorkSchedule/provider.jsx";
import {useScheduleContext} from "../contexts/Schedule/provider.jsx";
import {useSpecialistContext} from "../contexts/Specialist/provider.jsx";
import {useDayContext} from "../contexts/Day/provider.jsx";
import {useMemo} from "react";

/**
 *
 * @returns {{generalSchedule: Object<string|number, Object<Date, Array<{
 *       start: Date, end: Date, patient: {name: string, type: string}, status: "booked" | "confirmed" | "free" | "na"
 *       }>>>,
 *       generalWorkSchedule: Object<string|number, Object<Date, Array<{start: Date, end: Date}>>>,
 *       workSchedule: Array<{start: Date, end: Date},
 *       schedule: Array<{
 *       start: Date, end: Date, patient: {name: string, type: string}, status: "booked" | "confirmed" | "free" | "na"
 *       }>>}}
 *       Расписания по конкретному пользователю и дате
 */
export default () => {
    const [generalWorkSchedule, setGeneralWorkSchedule] = useWorkScheduleContext();
    const [generalSchedule, setGeneralSchedule] = useScheduleContext()
    const specialist = useSpecialistContext();
    const date = useDayContext();
    const workSchedule = useMemo(() => {
        return generalWorkSchedule?.[specialist]?.[date] || [];
    }, [generalWorkSchedule, specialist, date]);
    const schedule = useMemo(() => {
        return generalSchedule?.[specialist]?.[date] || [];
    }, [generalSchedule, specialist, date]);
    return {
        workSchedule: workSchedule,
        schedule: schedule,
        generalWorkSchedule: generalWorkSchedule,
        generalSchedule: generalSchedule,
        setGeneralWorkSchedule: setGeneralWorkSchedule,
        setGeneralSchedule: setGeneralSchedule
    };
}