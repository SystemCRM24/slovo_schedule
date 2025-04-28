import './App.css'
import DateRangePicker from "./components/ui/DateRangePicker/index.jsx";
import React, {useState} from "react";
import {Container} from "react-bootstrap";
import Schedule from "./components/Schedule/index.jsx";
import {WorkScheduleContext} from "./contexts/WorkSchedule/context.js";
import {ScheduleContext} from "./contexts/Schedule/context.js";

function App() {
    const [dates, setDates] = useState({fromDate: undefined, toDate: undefined});
    const [schedule, setSchedule] = useState({});
    const [workSchedule, setWorkSchedule] = useState({});
    const onDatesChange = e => {
        const dateType = e.target.name;
        setDates({...dates, [dateType]: e.target.valueAsDate,});
    }
    return (
        <>
            <Container fluid>
                <DateRangePicker onChange={onDatesChange} dates={dates}/>
            </Container>
            <WorkScheduleContext.Provider value={[workSchedule, setWorkSchedule]}>
                <ScheduleContext.Provider value={[schedule, setSchedule]}>
                    <Schedule {...dates} />
                </ScheduleContext.Provider>
            </WorkScheduleContext.Provider>
        </>
    )
}

export default App
