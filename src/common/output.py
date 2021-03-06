# -*- coding: utf-8 -*-
import itertools

from datetime import datetime
from src.extra import utils


class IPSorter:
    _tmp_file = None
    temp_fh = None

    @staticmethod
    def _is_ip_in_slice(ip, genexpr, n):
        _, genexpr_cp = itertools.tee(genexpr)

        if ip in itertools.islice(genexpr_cp, 0, n):
            return True

        return False

    @staticmethod
    def _get_ip_from_line(line):
        if line.startswith('http'):
            els = line.split(':')
            return f'{els[0]}:{els[1]}'

        return line.split(':')[0]

    @property
    def _ips_from_file(self):
        return (self._get_ip_from_line(line) for line in self.temp_fh)

    def get_uniq_ips(self):
        all_ips, all_ips_cp = itertools.tee(self._ips_from_file)

        return (
            ip for n, ip in enumerate(all_ips) if not self._is_ip_in_slice(ip, all_ips_cp, n)
        )


class Output(IPSorter):
    _data_block_size = 10_000
    _date_now = datetime.now().strftime('%d-%m-%y-%H-%M-%S')

    def __init__(self, *args, **kwargs):
        super(Output, self).__init__(*args, **kwargs)
        self.output_to = kwargs.get('output_to', 'file')
        self._output_writers = {
            'file': self._to_file,
        }

        self._final_file = utils.get_file_path('src', f'{kwargs.get("final_file")}-final-{self._date_now}.prm')
        self._final_fh = open(self._final_file, 'a')

    def _get_final_msg(self):
        msg = f'\u001b[31m>> \u001b[36mThe output file is located by path -> \u001b[33m{self._final_file}'

        return msg

    def _to_file(self, data):
        self._final_fh.write(data)

    def _final_actions(self):
        self.temp_fh.close()
        self._final_fh.close()

        utils.remove_file(self._tmp_file)
        print(self._get_final_msg())

    @staticmethod
    def _get_ports_from_line(line):
        if line.startswith('http'):
            return ''.join(line.split(':')[2:]).replace('\n', '').strip() + ' '

        return line.split(':')[1].replace('\n', '').strip() + ' '

    def _find_ports_for_each_ip(self, writer, ip):
        ports = ''

        with open(self._tmp_file, 'r') as file:
            for line in file:
                if ip + ':' in line:
                    ports += self._get_ports_from_line(line)

        writer(f'{ip}:{ports}\n')

    def _get_ips_with_ports_for_ips_block(self, ips_block):
        writer = self._output_writers.get(self.output_to)
        [self._find_ports_for_each_ip(writer, ip) for ip in ips_block]

    @staticmethod
    def _is_contains_elements(genexpr):
        count = 0

        for _ in genexpr:
            count += 1
            break

        return True if count > 0 else False

    def output(self, tmp_file):
        self._tmp_file = tmp_file
        self.temp_fh = open(self._tmp_file, 'r+')
        ips = self.get_uniq_ips()

        while True:
            ips_slice, ips_slice_cp = itertools.tee(
                itertools.islice(ips, 0, self._data_block_size)
            )

            if not self._is_contains_elements(ips_slice_cp):
                break

            self._get_ips_with_ports_for_ips_block(ips_slice)

        self._final_actions()
