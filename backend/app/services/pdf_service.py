"""
PDF generation service for reports
"""

import io
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime
import base64

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger = structlog.get_logger()
    logger.warning("ReportLab not available, PDF generation will use mock service")

logger = structlog.get_logger()

class PDFService:
    """Service for generating PDF reports"""
    
    def __init__(self):
        self.styles = None
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
        
        if not REPORTLAB_AVAILABLE:
            return
        
        # Custom styles
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#005F73')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#005F73')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
    
    async def generate_weekly_report(self, report_data: Dict[str, Any]) -> bytes:
        """Generate weekly trading report PDF"""
        
        try:
            if not REPORTLAB_AVAILABLE:
                return await self._generate_mock_pdf(report_data)
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            # Build the story
            story = []
            
            # Title
            story.append(Paragraph("TradeQuest Weekly Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 12))
            
            # Report period
            period_text = f"Week of {report_data.get('week_start', 'Unknown')} to {report_data.get('week_end', 'Unknown')}"
            story.append(Paragraph(period_text, self.styles['CustomBody']))
            story.append(Spacer(1, 20))
            
            # Key Metrics Section
            story.append(Paragraph("Key Metrics", self.styles['CustomHeading']))
            
            metrics_data = [
                ['Metric', 'Value'],
                ['Total Trades', str(report_data.get('total_trades', 0))],
                ['Win Rate', f"{report_data.get('win_rate', 0):.1%}"],
                ['Total P&L', f"${report_data.get('total_pnl', 0):.2f}"],
                ['Consistency Score', f"{report_data.get('consistency_score', 0):.1%}"],
                ['Average Win', f"${report_data.get('avg_win', 0):.2f}"],
                ['Average Loss', f"${report_data.get('avg_loss', 0):.2f}"],
                ['Profit Factor', f"{report_data.get('profit_factor', 0):.2f}"]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005F73')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 20))
            
            # Action Items Section
            story.append(Paragraph("Action Items", self.styles['CustomHeading']))
            
            action_items = report_data.get('action_items', [])
            if action_items:
                for item in action_items:
                    story.append(Paragraph(f"• {item}", self.styles['CustomBody']))
                    story.append(Spacer(1, 6))
            else:
                story.append(Paragraph("No specific action items for this week.", self.styles['CustomBody']))
            
            story.append(Spacer(1, 20))
            
            # Habits Summary Section
            habits_summary = report_data.get('habits_summary', {})
            if habits_summary:
                story.append(Paragraph("Trading Habits Summary", self.styles['CustomHeading']))
                
                habits_data = [
                    ['Metric', 'Value'],
                    ['Most Traded Symbol', habits_summary.get('most_traded_symbol', 'N/A')],
                    ['Most Active Hour', f"{habits_summary.get('most_active_hour', 'N/A')}:00"],
                    ['Symbol Diversity', str(habits_summary.get('symbol_diversity', 0))]
                ]
                
                habits_table = Table(habits_data, colWidths=[3*inch, 2*inch])
                habits_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFC300')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(habits_table)
                story.append(Spacer(1, 20))
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | TradeQuest Educational Platform"
            story.append(Paragraph(footer_text, self.styles['CustomBody']))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info("Weekly report PDF generated successfully")
            return pdf_content
            
        except Exception as e:
            logger.error("Failed to generate weekly report PDF", error=str(e))
            return await self._generate_mock_pdf(report_data)
    
    async def generate_daily_report(self, report_data: Dict[str, Any]) -> bytes:
        """Generate daily trading report PDF"""
        
        try:
            if not REPORTLAB_AVAILABLE:
                return await self._generate_mock_pdf(report_data)
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            story = []
            
            # Title
            story.append(Paragraph("TradeQuest Daily Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 12))
            
            # Date
            date_text = f"Date: {report_data.get('date', 'Unknown')}"
            story.append(Paragraph(date_text, self.styles['CustomBody']))
            story.append(Spacer(1, 20))
            
            # Daily Metrics
            story.append(Paragraph("Daily Performance", self.styles['CustomHeading']))
            
            metrics_data = [
                ['Metric', 'Value'],
                ['Trades Today', str(report_data.get('trades_count', 0))],
                ['Total P&L', f"${report_data.get('total_pnl', 0):.2f}"],
                ['Win Rate', f"{report_data.get('win_rate', 0):.1%}"],
                ['Rule Adherence', f"{report_data.get('adherence_score', 0):.1%}"]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005F73')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metrics_table)
            story.append(Spacer(1, 20))
            
            # AI Note
            story.append(Paragraph("AI Analysis", self.styles['CustomHeading']))
            ai_note = report_data.get('ai_note', 'No analysis available.')
            story.append(Paragraph(ai_note, self.styles['CustomBody']))
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | TradeQuest Educational Platform"
            story.append(Paragraph(footer_text, self.styles['CustomBody']))
            
            # Build PDF
            doc.build(story)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info("Daily report PDF generated successfully")
            return pdf_content
            
        except Exception as e:
            logger.error("Failed to generate daily report PDF", error=str(e))
            return await self._generate_mock_pdf(report_data)
    
    async def _generate_mock_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """Generate mock PDF for development"""
        
        # Create a simple text-based "PDF" for development
        content = f"""
TradeQuest Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Report Data:
{report_data}

This is a mock PDF for development purposes.
In production, this would be a properly formatted PDF document.
        """.encode('utf-8')
        
        logger.info("Mock PDF generated")
        return content
    
    async def generate_trade_summary_pdf(self, trades: List[Dict[str, Any]], summary_data: Dict[str, Any]) -> bytes:
        """Generate trade summary PDF"""
        
        try:
            if not REPORTLAB_AVAILABLE:
                return await self._generate_mock_pdf(summary_data)
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            story = []
            
            # Title
            story.append(Paragraph("Trade Summary Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 12))
            
            # Summary
            story.append(Paragraph("Summary", self.styles['CustomHeading']))
            
            summary_data_table = [
                ['Metric', 'Value'],
                ['Total Trades', str(len(trades))],
                ['Total P&L', f"${summary_data.get('total_pnl', 0):.2f}"],
                ['Win Rate', f"{summary_data.get('win_rate', 0):.1%}"],
                ['Average Win', f"${summary_data.get('avg_win', 0):.2f}"],
                ['Average Loss', f"${summary_data.get('avg_loss', 0):.2f}"]
            ]
            
            summary_table = Table(summary_data_table, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#005F73')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Individual Trades
            if trades:
                story.append(Paragraph("Individual Trades", self.styles['CustomHeading']))
                
                # Prepare trades data
                trades_data = [['Date', 'Symbol', 'Side', 'Qty', 'Price', 'P&L']]
                
                for trade in trades[:50]:  # Limit to 50 trades to avoid huge PDFs
                    trades_data.append([
                        trade.get('filled_at', '')[:10],  # Just the date part
                        trade.get('symbol', ''),
                        trade.get('side', ''),
                        f"{trade.get('qty', 0):.4f}",
                        f"${trade.get('avg_price', 0):.2f}",
                        f"${trade.get('pnl', 0):.2f}"
                    ])
                
                trades_table = Table(trades_data, colWidths=[1*inch, 1*inch, 0.5*inch, 1*inch, 1*inch, 1*inch])
                trades_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFC300')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                
                story.append(trades_table)
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | TradeQuest Educational Platform"
            story.append(Paragraph(footer_text, self.styles['CustomBody']))
            
            # Build PDF
            doc.build(story)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info("Trade summary PDF generated successfully")
            return pdf_content
            
        except Exception as e:
            logger.error("Failed to generate trade summary PDF", error=str(e))
            return await self._generate_mock_pdf(summary_data)
