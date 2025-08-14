import './App.css';
import DateRangePicker from "./components/ui/DateRangePicker/index.jsx";
import React, { useMemo, useState } from "react";
import { Button, Container, ButtonGroup } from "react-bootstrap";
import Schedule from "./components/Schedule/index.jsx";
import { WorkScheduleContextProvider } from "./contexts/WorkSchedule/provider.jsx";
import { ScheduleContextProvider } from "./contexts/Schedule/provider.jsx";
import { AppContextProvider } from "./contexts/App/provider.jsx";
import Statistics from './Statistics/main/index.jsx';


function App() {
    const [tab, setTab] = useState('schedule');

    const content = useMemo(
        () => {
            if ( tab === 'schedule' ) {
                return (
                    <WorkScheduleContextProvider schedule={{}}>
                        <ScheduleContextProvider schedule={{}}>
                            <Schedule />
                        </ScheduleContextProvider>
                    </WorkScheduleContextProvider>
                );
            } else {
                return <Statistics/>;
            }
        },
        [tab]
    );

    return (
        <AppContextProvider>
            <Container fluid className={'mt-2 mb-2 d-flex gap-3 justify-content-between'}>
                <DateRangePicker />
                <ButtonGroup>
                    <Button
                        variant={tab === 'schedule' ? 'primary' : 'outline-primary'}
                        onClick={e => setTab('schedule')}
                    >
                        Расписание
                    </Button>
                    <Button
                        variant={tab === 'statistics' ? 'primary' : 'outline-primary'}
                        onClick={e => setTab('statistics')}
                    >
                        Статистика
                    </Button>
                </ButtonGroup>
            </Container>
            {content}
        </AppContextProvider>
    );
}

export default App;