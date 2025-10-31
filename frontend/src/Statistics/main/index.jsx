import { useContext, useEffect, useMemo, useState } from "react";
import apiClient from "../../api";
import { AppContext } from "../../contexts/App/context";
import { Table } from "react-bootstrap";

import { StatisticsContextProvider } from "../context/provider";
import './Schedule.css';
import Headers from "../headers";
import Rows from "../rows";


function Statistics() {
    const { dates, setHolidays } = useContext(AppContext);
    const [specialists, setSpecialists] = useState(null);
    const [schedules, setSchedule] = useState(null);
    const [appointments, setAppointments] = useState(null);

    useEffect(() => {
        (async () => {
            const [specialists, constants] = await Promise.all([
                apiClient.getSpecialists(),
                apiClient.updateConstants()
            ]);
            setSpecialists(specialists);
        })();
    }, []);

    useEffect(() => {
        (async () => {
            const { fromDate, toDate } = dates;
            if (fromDate && toDate) {
                setAppointments(null);
                setSchedule(null);
                const [scheduleData, workScheduleData, holidaysData] = await Promise.all([
                    apiClient.getSchedules(fromDate, toDate),
                    apiClient.getWorkSchedules(fromDate, toDate),
                    apiClient.getHolidays(fromDate, toDate)
                ]);
                setAppointments(scheduleData);
                setSchedule(workScheduleData);
                setHolidays(new Set(holidaysData));
            }
        })();
    }, [dates, setSchedule, setAppointments]);

    const sortedSpecialists = useMemo(
        () => {
            if ( specialists === null ) {
                return [];
            }
            const specs = Object.values(specialists);
            specs.sort((a, b) => a.sort_index - b.sort_index);
            return specs;
        },
        [specialists]
    );

    return (dates.fromDate && dates.toDate && sortedSpecialists.length > 0) && (
        <Table id='schedule-table' bordered responsive>
            <StatisticsContextProvider schedules={schedules} appointments={appointments}>
                <Headers specialists={sortedSpecialists}/>
                <Rows dates={dates} specialists={sortedSpecialists}></Rows>
            </StatisticsContextProvider>
        </Table>
    );
}

export default Statistics;