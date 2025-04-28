import React from "react";
import {Button, Modal} from "react-bootstrap";

export default function CustomModal({
    show,
    handleClose, 
    handlePrimaryBtnClick, 
    primaryBtnText, 
    title,
    size = 'xl',
    children
}) {
    return (
        <Modal show={show} onHide={handleClose} size={size} centered>
            <Modal.Header closeButton>
                <Modal.Title>{title}</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {children}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={handleClose}>
                    Закрыть
                </Button>
                {(primaryBtnText && handlePrimaryBtnClick) &&
                    <Button variant="primary" onClick={handlePrimaryBtnClick}>
                        {primaryBtnText}
                    </Button>}
            </Modal.Footer>
        </Modal>
    );
}
