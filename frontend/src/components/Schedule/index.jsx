import React, {Suspense, useEffect, useState, useMemo} from 'react';
import {Spinner, Table} from "react-bootstrap";

import DaySchedule from '../DaySchedule';
import apiClient from "../../api/";
import {useScheduleContext} from "../../contexts/Schedule/provider.jsx";
import {useWorkScheduleContext} from "../../contexts/WorkSchedule/provider.jsx";
import {SpecialistContextProvider} from "../../contexts/Specialist/provider.jsx";
import {DayContextProvider} from "../../contexts/Day/provider.jsx";
import {AllSpecialistsContextProvider} from "../../contexts/AllSpecialists/provider.jsx";
import {ChildrenContextProvider} from "../../contexts/Children/provider.jsx";

import "./Schedule.css"



const Legenda = () => {
    const style = {
        listStyle: 'none', 
        height: 30, 
        display: "flex",
        justifyContent: "space-around", 
        marginTop: '.75rem'
    };
    const items = {'free': 'Свободно', 'booked': "Забронировано", 'confirmed': "Подтверждено"};
    return (
        <ul
            style={style}
        >
            {Object.entries(items).map(
                ([status, label]) => {
                    return (
                        <li 
                            className={`me-2 d-flex align-items-center justify-content-between`}
                            style={{float: "left"}}
                            key={`${status}_${label}`}
                        >
                            <span 
                                className={`status-${status}`}
                                style={{width: 12, height: 12, float: "left", marginRight: ".5rem"}}
                            >
                                {label}
                            </span>
                        </li>
                    )
                }
            )}
        </ul>
    );
}


const Schedule = ({fromDate, toDate}) => {
    const [specialists, setSpecialists] = useState({});
    const [children, setChildren] = useState({})
    const [schedule, setSchedule] = useScheduleContext();
    const [workSchedule, setWorkSchedule] = useWorkScheduleContext();

    // const apiClient = apiClient;

    useEffect(() => {
        (async () => {
            const [allSpecialists, children] = await Promise.all(
                [
                    apiClient.getSpecialists(),
                    apiClient.getClients()
                ]
            )
            setSpecialists(allSpecialists);
            setChildren(children);
        })();
    }, []);

    useEffect(() => {
        (async () => {
            if (fromDate && toDate) {
                const [scheduleData, workScheduleData] = await Promise.all([
                    apiClient.getSchedules(fromDate, toDate),
                    apiClient.getWorkSchedules(fromDate, toDate)
                ]);
                console.log(scheduleData);
                setSchedule(scheduleData);
                setWorkSchedule(workScheduleData);
            }
        })();
    }, [fromDate, setSchedule, setWorkSchedule, toDate]);

    const headers = useMemo(
        () => {
            const headers = [];
            for (const [id, specialist] of Object.entries(specialists)) {
                const codes = specialist.departments.join(', ');
                headers.push((
                    <th
                        scope="col"
                        style={{minWidth: '220px', whiteSpace: 'pre-wrap'}}
                        key={`specialist_${id}_header`}
                    >
                        {specialist.name + '\n' + codes}
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
            while (currentDate <= toDate) {
                const row = [];
                const dayOfWeek = currentDate.toLocaleString('ru-RU', {weekday: 'long'});
                const date = currentDate.toLocaleDateString();
                row.push((
                    <th 
                        // scope={'row'} 
                        key={date}
                        style={{minHeight: '100px', height: 'auto'}}
                    >
                        {dayOfWeek}<br/>{date}
                    </th>
                ));
                const scheduleDate = new Date(currentDate)
                for (const specialistId of Object.keys(specialists)) {
                    const cell = (
                        <SpecialistContextProvider key={`${specialistId}_${date}_ctx`} specialist={specialistId}>
                            <DayContextProvider day={scheduleDate} key={`${date}_ctx`}>
                                <DaySchedule key={`${specialistId}_${date}_schedule`}/>
                            </DayContextProvider>
                        </SpecialistContextProvider>
                    );
                    row.push(cell)
                }
                rows.push((<tr key={`row_${date}`}>{row}</tr>))
                currentDate.setDate(currentDate.getDate() + 1);
            }
            return rows;
        },
        [fromDate, toDate, specialists]
    );
    return (fromDate && toDate) && (
        <Suspense fallback={<Spinner animation={"grow"}/>}>
            <AllSpecialistsContextProvider specialists={specialists}>
                <ChildrenContextProvider childrenElements={children}>
                    <Table 
                        id='schedule-table'
                        bordered 
                        responsive
                    >
                        <thead>
                            <tr>
                                <th scope="col" style={{minWidth: '130px'}}/>{headers}
                            </tr>
                        </thead>
                        <tbody>{rows}</tbody>
                    </Table>
                </ChildrenContextProvider>
            </AllSpecialistsContextProvider>
        </Suspense>
    );
};

export default Schedule;