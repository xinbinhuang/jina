import argparse
from abc import ABC
from typing import Union, Dict

from ..base import BaseRuntime
from ...zmq import Zmqlet, send_ctrl_message


class ZMQRuntime(BaseRuntime, ABC):

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.ctrl_addr = Zmqlet.get_ctrl_address(self.args.host, self.args.port_ctrl, self.args.ctrl_with_ipc)[0]

    def cancel(self):
        send_ctrl_message(self.ctrl_addr, 'TERMINATE', timeout=self.args.timeout_ctrl)

    @property
    def status(self):
        return send_ctrl_message(self.ctrl_addr, 'STATUS', timeout=self.args.timeout_ctrl)

    @property
    def is_ready(self) -> bool:
        status = self.status
        return status and status.is_ready


class ZMQManyRuntime(BaseRuntime, ABC):
    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        self.many_ctrl_addr = []
        if isinstance(args, Dict):
            first_args = self.args['peas'][0]
            self.timeout_ctrl = first_args.timeout_ctrl
            self.host = first_args.host
            self.port_expose = first_args.port_expose
            self.remote_type = first_args.remote_type
            for args in self.args['peas']:
                ctrl_addr, _ = Zmqlet.get_ctrl_address(args.host, args.port_ctrl, args.ctrl_with_ipc)
                self.many_ctrl_addr.append(ctrl_addr)
        elif isinstance(args, argparse.Namespace):
            self.many_ctrl_addr.append(Zmqlet.get_ctrl_address(args.host, self.args.port_ctrl, args.ctrl_with_ipc)[0])
            self.timeout_ctrl = args.timeout_ctrl
            self.host = args.host
            self.port_expose = args.port_expose
            self.remote_type = args.remote_type

    def cancel(self):
        # TODO: can use send_message_async to avoid sequential waiting
        for ctrl_addr in self.many_ctrl_addr:
            send_ctrl_message(ctrl_addr, 'TERMINATE', timeout=self.timeout_ctrl)

    @property
    def status(self):
        # TODO: can use send_ctrl_message to avoid sequential waiting
        result = []
        for ctrl_addr in self.many_ctrl_addr:
            result.append(send_ctrl_message(ctrl_addr, 'STATUS', timeout=self.timeout_ctrl))
        return result

    @property
    def is_ready(self) -> bool:
        status = self.status
        return status and all(s.is_ready for s in status)
