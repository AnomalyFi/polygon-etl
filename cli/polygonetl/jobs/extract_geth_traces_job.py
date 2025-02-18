# MIT License
#
# Copyright (c) 2018 Evgeniy Filatov, evgeniyfilatov@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from blockchainetl_common.jobs.base_job import BaseJob
from polygonetl.executors.batch_work_executor import BatchWorkExecutor
from polygonetl.mappers.geth_trace_mapper import EthGethTraceMapper
from polygonetl.mappers.trace_mapper import EthTraceMapper
from polygonetl.service.trace_id_calculator import calculate_trace_ids
from polygonetl.service.trace_status_calculator import calculate_trace_statuses


class ExtractGethTracesJob(BaseJob):
    def __init__(self, traces_iterable, batch_size, max_workers, item_exporter):
        self.traces_iterable = traces_iterable

        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers, name='ExtractGethTraces')
        self.item_exporter = item_exporter

        self.trace_mapper = EthTraceMapper()
        self.geth_trace_mapper = EthGethTraceMapper()

    def _start(self):
        self.item_exporter.open()

    def _export(self):
        self.batch_work_executor.execute(
            self.traces_iterable, self._extract_geth_traces
        )

    def _extract_geth_traces(self, geth_traces):
        all_traces = []

        for geth_trace_dict in geth_traces:
            geth_trace = self.geth_trace_mapper.json_dict_to_geth_trace(geth_trace_dict)
            traces = self.trace_mapper.geth_trace_to_traces(geth_trace)
            all_traces.extend(traces)

        calculate_trace_statuses(all_traces)
        calculate_trace_ids(all_traces)

        for trace in all_traces:
            self.item_exporter.export_item(self.trace_mapper.trace_to_dict(trace))

    def _end(self):
        self.batch_work_executor.shutdown()
        self.item_exporter.close()
