import React, {Suspense, useEffect, useState, useMemo} from 'react';
import {Spinner, Table} from "react-bootstrap";

import DaySchedule from '../DaySchedule';
import apiClient from "../../api/";
import {WorkScheduleContext} from "../../contexts/WorkSchedule/context.js";
import {ScheduleContext} from "../../contexts/Schedule/context.js";
import {useScheduleContext} from "../../contexts/Schedule/provider.jsx";
import {useWorkScheduleContext} from "../../contexts/WorkSchedule/provider.jsx";


const Schedule = ({fromDate, toDate}) => {
    const [specialists, setSpecialists] = useState([]);
    const [schedule, setSchedule] = useScheduleContext();
    const [workSchedule, setWorkSchedule] = useWorkScheduleContext();

    useEffect(() => {
        (async () => {
            setSpecialists(await apiClient.getSpecialists());
        })();
    }, []);

    useEffect(() => {
        (async () => {
            if (fromDate && toDate) {
                const [scheduleData, workScheduleData] = await Promise.all([
                    apiClient.getSchedule(fromDate, toDate),
                    apiClient.getWorkSchedule(fromDate, toDate)
                ]);
                setSchedule(scheduleData);
                setWorkSchedule(workScheduleData);
            }
        })();
    }, [fromDate, toDate]);

    const headers = useMemo(
        () => {
            const headers = [];
            for (const [name, attr] of Object.entries(specialists)) {
                const codes = attr.departments.join(', ');
                headers.push((
                    <th
                        scope="col"
                        style={{width: 400, whiteSpace: 'pre-wrap'}}
                        key={name}
                    >
                        {name + '\n' + codes}
                    </th>
                ));
            }
            return headers;
        },
        [specialists]
    );

    const rows = useMemo(
        () => {
            const rows = [];
            let currentDate = new Date(fromDate);
            const style = {height: '800px'};
            while (currentDate <= toDate) {
                const row = [];
                const dayOfWeek = currentDate.toLocaleString('ru-RU', {weekday: 'long'});
                const date = currentDate.toLocaleDateString();
                row.push((
                    <th scope={'row'} key={date}>{dayOfWeek}<br/>{date}</th>
                ));
                for (const specialist of Object.keys(specialists)) {
                    const cell = (
                        <DaySchedule key={`${specialist}_${date}`} specialist={specialist} date={new Date(currentDate)}/>);
                    row.push(cell)
                }
                rows.push((<tr style={style} key={`row_${date}`}>{row}</tr>))
                currentDate.setDate(currentDate.getDate() + 1);
            }
            return rows;
        },
        [fromDate, toDate, specialists]
    );
    return (fromDate && toDate) && (
        <WorkScheduleContext.Provider value={[workSchedule, setWorkSchedule]}>
            <ScheduleContext.Provider value={[schedule, setSchedule]}>
                <Suspense fallback={<Spinner animation={"grow"}/>}>
                    <Table bordered responsive className={'mt-3'} style={{width: `${30 * specialists.length}%`}}>
                        <thead>
                        <tr>
                            <th scope="col" style={{width: 200}}/>
                            {headers}
                        </tr>
                        </thead>
                        <tbody>
                        {rows}
                        </tbody>
                    </Table>
                </Suspense>
            </ScheduleContext.Provider>
        </WorkScheduleContext.Provider>
    );
};

export default React.memo(Schedule);